import tempfile
import os

import requests
from packaging import version

from utils.logger import Logger
from utils.threads import BaseThread, ThreadManager
from utils.signals import Signal


class UpdateCheckThread(BaseThread):
    """版本检查线程"""

    def __init__(self, current_version, api_url):
        super().__init__()
        self.current_version = current_version
        self.api_url = api_url
        self.logger = Logger()
        # 添加 User-Agent 避免 GitHub API 限制
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/vnd.github.v3+json'
        }

    def run(self):
        try:
            self.logger.info(f"开始检查更新，当前版本: {self.current_version}")

            # 发送请求
            response = requests.get(
                self.api_url,
                headers=self.headers,
                timeout=30,  # 30秒超时
                verify=True
            )

            if not response.ok:
                error_msg = f"API请求失败: HTTP {response.status_code}"
                self.logger.error(error_msg)
                self.error.emit(error_msg)
                return

            latest = response.json()
            if not latest:
                self.logger.error("API响应为空")
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
            error_msg = "检查更新超时，请检查网络连接"
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


class UpdateDownloadThread(BaseThread):
    """更新下载线程"""
    progress = Signal(int)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.logger = Logger()

    def run(self):
        try:
            self.logger.info(f"开始下载更新")

            response = requests.get(
                self.url,
                stream=True,
                timeout=60  # 下载超时时间设置为60秒
            )

            if not response.ok:
                self.error.emit(f"下载失败: HTTP {response.status_code}")
                return

            total_size = int(response.headers.get('content-length', 0))

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.exe')
            downloaded = 0
            last_progress = 0
            block_size = 8192

            for data in response.iter_content(block_size):
                if not self._check_running():
                    temp_file.close()
                    os.unlink(temp_file.name)
                    return

                if not data:
                    break

                downloaded += len(data)
                temp_file.write(data)

                if total_size:
                    progress = int((downloaded / total_size) * 100)
                    if progress > last_progress:
                        self.progress.emit(progress)
                        last_progress = progress

            temp_file.close()
            self.logger.info("更新下载完成")
            self.success.emit(temp_file.name)

        except requests.exceptions.Timeout:
            error_msg = "下载超时，请检查网络连接"
            self.logger.error(error_msg)
            self.error.emit(error_msg)
        except requests.exceptions.SSLError:
            error_msg = "SSL证书验证失败"
            self.logger.error(error_msg)
            self.error.emit(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"下载失败: {str(e)}"
            self.logger.error(error_msg)
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"下载失败: {str(e)}"
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
        if hasattr(self, '_callback'):
            self._callback(result)

    def _on_check_error(self, error):
        """检查更新出错处理"""
        error_msg = f"检查更新失败: {error}"
        self.logger.error(error_msg)
        if hasattr(self, '_callback'):
            self._callback((False, {'error': error_msg}))
