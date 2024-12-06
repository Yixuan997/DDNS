import tempfile
import os
import json

import requests
from packaging import version

from utils.logger import Logger
from utils.threads import BaseThread, ThreadManager
from utils.signals import Signal


class UpdateMirrors:
    """更新镜像站点管理"""

    # 镜像站点列表，按优先级排序
    MIRRORS = [
        "https://ghp.ci",  # ghp.ci镜像（最快）
        "https://github.moeyy.xyz",  # moeyy镜像
        "https://mirror.ghproxy.com",  # ghproxy镜像
        "https://gh-proxy.com",  # gh-proxy镜像
        "https://x.haod.me"  # haod.me镜像
    ]

    @staticmethod
    def get_download_urls(original_url):
        """
        获取所有可用的下载地址
        Args:
            original_url: 原始GitHub下载地址
        Returns:
            list: 所有可用的下载地址列表
        """
        urls = []

        # 确保原始URL是完整的GitHub URL
        if not original_url.startswith("https://github.com/"):
            return [original_url]

        # 对于每个镜像站点，在原始URL前面加上镜像站点地址
        for mirror in UpdateMirrors.MIRRORS:
            mirror_url = f"{mirror}/{original_url}"
            urls.append(mirror_url)

        return urls


class UpdateDownloadThread(BaseThread):
    """更新下载线程"""
    progress = Signal(int)

    def __init__(self, url):
        super().__init__()
        self.original_url = url
        self.logger = Logger()
        self.current_url_index = 0
        self.download_urls = UpdateMirrors.get_download_urls(url)


    def try_next_mirror(self):
        """尝试下一个镜像站点"""
        self.current_url_index += 1
        has_next = self.current_url_index < len(self.download_urls)
        if has_next:
            next_url = self.download_urls[self.current_url_index]
            mirror_name = next_url.split("/")[2]
            self.logger.info(f"切换到镜像: {mirror_name}")
        return has_next

    def run(self):
        while True:
            try:
                current_url = self.download_urls[self.current_url_index]
                mirror_name = current_url.split("/")[2]  # 获取镜像域名
                self.logger.info(f"开始使用镜像下载: {mirror_name}")

                response = requests.get(
                    current_url,
                    stream=True,
                    timeout=15,
                    verify=True
                )

                if not response.ok:
                    self.logger.error(f"镜像 {mirror_name} 下载失败: HTTP {response.status_code}")
                    if self.try_next_mirror():
                        continue
                    self.error.emit(f"所有镜像下载失败")
                    return

                total_size = int(response.headers.get('content-length', 0))
                if total_size == 0:
                    self.logger.error(f"镜像 {mirror_name} 返回内容为空")
                    if self.try_next_mirror():
                        continue
                    self.error.emit(f"下载内容为空")
                    return

                self.logger.debug(f"文件大小: {total_size / 1024 / 1024:.2f}MB")
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.exe')
                downloaded = 0
                last_progress = 0
                block_size = 8192

                for data in response.iter_content(block_size):
                    if not self._check_running():
                        temp_file.close()
                        os.unlink(temp_file.name)
                        self.logger.debug("下载已取消")
                        return

                    if not data:
                        break

                    downloaded += len(data)
                    temp_file.write(data)

                    if total_size:
                        progress = int((downloaded / total_size) * 100)
                        if progress > last_progress:
                            self.progress.emit(progress)
                            if progress % 25 == 0:  # 每25%记录一次进度
                                self.logger.info(f"下载进度: {progress}%")
                            last_progress = progress

                temp_file.close()

                # 验证下载是否完整
                if downloaded != total_size:
                    self.logger.error(f"下载不完整: {downloaded}/{total_size}")
                    os.unlink(temp_file.name)
                    if self.try_next_mirror():
                        continue
                    self.error.emit(f"下载文件不完整")
                    return

                self.logger.info("更新下载完成")
                self.success.emit(temp_file.name)
                return

            except requests.exceptions.RequestException as e:
                mirror_name = self.download_urls[self.current_url_index].split("/")[2]
                self.logger.error(f"镜像 {mirror_name} 下载失败: {str(e)}")
                if self.try_next_mirror():
                    continue
                self.error.emit(f"所有镜像下载失败")
                return
            except Exception as e:
                mirror_name = self.download_urls[self.current_url_index].split("/")[2]
                self.logger.error(f"下载失败: {str(e)}")
                self.error.emit(str(e))
                return
            finally:
                if not self._check_running():
                    self.finished.emit()


class UpdateCheckThread(BaseThread):
    """版本检查线程"""

    def __init__(self, current_version, api_url):
        super().__init__()
        self.current_version = current_version
        self.api_url = api_url
        self.logger = Logger()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/vnd.github.v3+json'
        }

    def run(self):
        try:
            # 发送请求
            response = requests.get(
                self.api_url,
                headers=self.headers,
                timeout=30,
                verify=True
            )

            if not response.ok:
                error_msg = f"GitHub API请求失败: HTTP {response.status_code}"
                self.logger.error(error_msg)
                self.error.emit(error_msg)
                return

            latest = response.json()
            if not latest:
                self.logger.error("GitHub API响应为空")
                self.error.emit("API响应为空")
                return

            if 'tag_name' not in latest:
                self.logger.error("无效的版本信息")
                self.error.emit("无效的版本信息")
                return

            latest_version = latest['tag_name'].lstrip('v')
            has_update = version.parse(latest_version) > version.parse(self.current_version)

            if has_update:
                if 'assets' not in latest or not latest['assets']:
                    self.logger.error("未找到下载资源")
                    self.error.emit("未找到下载资源")
                    return

                update_info = {
                    'version': latest_version,
                    'description': latest.get('body', '无更新说明'),
                    'download_url': latest['assets'][0]['browser_download_url']
                }
                self.logger.info(f"发现新版本: {latest_version}")
                self.success.emit((True, update_info))
            else:
                self.logger.info("当前已是最新版本")
                self.success.emit((False, None))

        except requests.exceptions.Timeout:
            error_msg = "GitHub API请求超时，请检查网络连接"
            self.logger.error(error_msg)
            self.error.emit(error_msg)
        except requests.exceptions.SSLError as e:
            error_msg = f"SSL证书验证失败: {str(e)}"
            self.logger.error(error_msg)
            self.error.emit(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            self.logger.error(error_msg)
            self.error.emit(error_msg)
        except version.InvalidVersion as e:
            error_msg = f"版本号格式错误: {str(e)}"
            self.logger.error(error_msg)
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"检查更新失败: {str(e)}"
            self.logger.error(error_msg)
            self.error.emit(error_msg)
        finally:
            self.finished.emit()


class Updater:
    CURRENT_VERSION = "1.0.0"
    GITHUB_API = "https://api.github.com/repos/Yixuan997/DDNS/releases/latest"

    def __init__(self):
        self.logger = Logger()
        self._thread_manager = ThreadManager.instance()
        self._main_window = None

    def check_update(self, callback):
        """
        检查更新
        Args:
            callback: 回调函数，接收 (has_update, update_info) 参数
        """
        try:
            self.logger.debug("开始检查更新...")
            self._callback = callback  # 保存回调函数
            check_thread = UpdateCheckThread(self.CURRENT_VERSION, self.GITHUB_API)

            # 连接信号前先断开之前的连接
            try:
                check_thread.success.disconnect()
                check_thread.error.disconnect()
            except:
                pass

            check_thread.success.connect(self._on_check_success)
            check_thread.error.connect(self._on_check_error)
            self._thread_manager.submit_thread(check_thread)

        except Exception as e:
            error_msg = f"启动更新检查失败: {str(e)}"
            self.logger.error(error_msg)
            if callback:
                callback((False, {'error': error_msg}))

    def _on_check_success(self, result):
        """检查成功的处理"""
        has_update, update_info = result
        if has_update:
            if 'download_url' in update_info:
                mirrors = UpdateMirrors()
                mirror_urls = mirrors.get_download_urls(update_info['download_url'])
        if hasattr(self, '_callback'):
            self._callback(result)

    def _on_check_error(self, error):
        """检查更新出错处理"""
        error_msg = f"检查更新失败: {error}"
        self.logger.error(error_msg)
        if hasattr(self, '_callback'):
            self._callback((False, {'error': error_msg}))
