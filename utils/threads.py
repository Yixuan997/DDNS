"""
@Project ：DDNS 
@File    ：threads.py
@IDE     ：PyCharm 
@Author  ：杨逸轩
@Date    ：2023/12/02
"""

import importlib
import os
import tempfile

import requests
from PySide6.QtCore import QThread, Signal

from utils.logger import Logger


class BaseThread(QThread):
    """基础线程类"""
    error = Signal(str)  # 错误信号
    finished = Signal()  # 完成信号
    success = Signal(object)  # 成功信号，可传递结果数据

    def __init__(self):
        super().__init__()
        self.logger = Logger()
        self._is_running = True

    def stop(self):
        """停止线程"""
        self._is_running = False
        self.wait()

    def _check_running(self):
        """检查线程是否应该继续运行"""
        return self._is_running


class DNSUpdateThread(BaseThread):
    """DNS更新线程"""

    def __init__(self, platform, ipv4, ipv6):
        super().__init__()
        self.platform = platform
        self.ipv4 = ipv4
        self.ipv6 = ipv6

    def run(self):
        if not self._check_running():
            return

        try:
            # 获取当前记录
            current_ipv4, current_ipv6 = self.platform.get_current_records()
            platform_key = self.platform.get_platform_key()
            record_type = self.platform.record_type

            # 选择要更新的IP
            current_ip = current_ipv4 if record_type == 'A' else current_ipv6
            new_ip = self.ipv4 if record_type == 'A' else self.ipv6

            self.logger.info(f"{platform_key} [{record_type}] - 当前记录: {current_ip or '无'}, 本地IP: {new_ip}")

            # 检查是否需要更新
            if new_ip and current_ip != new_ip and self._check_running():
                if self.platform.update_records(self.ipv4, self.ipv6):
                    self.success.emit(True)
                else:
                    self.error.emit("更新失败")
            else:
                self.logger.info(f"{platform_key} - 记录已是最新")
                self.success.emit(False)  # 不需要更新

        except Exception as e:
            self.logger.error(f"{self.platform.get_platform_key()} - 更新失败: {str(e)}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class DNSInitThread(BaseThread):
    """DNS平台初始化线程"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.platforms = {}

    def run(self):
        if not self._check_running():
            return

        try:
            config_data = self.config.load_config()
            platforms = config_data.get('platforms', {})

            for platform_name, platform_configs in platforms.items():
                if not self._check_running():
                    return

                try:
                    # 确保配置是列表形式
                    if not isinstance(platform_configs, list):
                        platform_configs = [platform_configs]

                    # 动态加载平台模块
                    module = importlib.import_module(f"dns_platforms.{platform_name}")
                    platform_class = getattr(module, f"{platform_name.title()}DNS")

                    # 处理每个配置
                    for config in platform_configs:
                        if not self._check_running():
                            return

                        try:
                            hostname = config.get('hostname', '@')
                            domain = config.get('domain', 'unknown')
                            full_domain = f"{hostname}.{domain}" if hostname != '@' else domain

                            platform_key = f"{platform_name}_{full_domain}_{config.get('record_type', 'A')}"
                            self.platforms[platform_key] = platform_class(config)

                            self.logger.info(f"DNS平台初始化成功: [{platform_name.upper()}][{full_domain}]")
                        except Exception as e:
                            self.logger.error(f"初始化DNS记录失败: [{platform_name}][{full_domain}] - {str(e)}")

                except Exception as e:
                    self.logger.error(f"加载DNS平台模块失败: {platform_name} - {str(e)}")

            self.success.emit(self.platforms)

        except Exception as e:
            self.logger.error(f"初始化DNS平台失败: {str(e)}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class IPCheckThread(BaseThread):
    """IP检查线程"""

    def __init__(self, ip_checker):
        super().__init__()
        self.ip_checker = ip_checker

    def run(self):
        if not self._check_running():
            return

        try:
            ipv4, ipv6 = self.ip_checker.get_current_ips()
            self.success.emit((ipv4 or '', ipv6 or ''))
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class UpdateDownloadThread(BaseThread):
    """更新下载线程"""
    progress = Signal(int)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        if not self._check_running():
            return

        try:
            response = requests.get(self.url, stream=True)
            total_size = int(response.headers.get('content-length', 0))

            temp_file = tempfile.NamedTemporaryFile(delete=False)
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
            self.success.emit(temp_file.name)

        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class ThreadManager:
    """线程管理器"""
    _instance = None
    _active_threads = set()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def submit_thread(self, thread):
        """提交线程"""
        ThreadManager._active_threads.add(thread)
        thread.finished.connect(lambda: self._on_thread_finished(thread))
        thread.start()
        return thread

    def _on_thread_finished(self, thread):
        """线程完成时的处理"""
        if thread in ThreadManager._active_threads:
            ThreadManager._active_threads.remove(thread)
            thread.deleteLater()

    def stop_all(self):
        """停止所有线程"""
        for thread in list(ThreadManager._active_threads):
            thread.stop()
            thread.wait()
            thread.deleteLater()
        ThreadManager._active_threads.clear()
