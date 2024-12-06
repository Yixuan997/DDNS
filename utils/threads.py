"""
@Project ：DDNS 
@File    ：threads.py
@IDE     ：PyCharm 
@Author  ：杨逸轩
@Date    ：2023/12/02
"""

from PySide6.QtCore import QThread, Signal
from concurrent.futures import ThreadPoolExecutor
import time

from utils.logger import Logger


class BaseThread(QThread):
    """基础线程类"""
    error = Signal(str)  # 错误信号
    finished = Signal()  # 完成信号

    def __init__(self):
        super().__init__()
        self.logger = Logger()
        self._is_running = True

    def stop(self):
        """停止线程"""
        self._is_running = False
        self.wait()

    def safe_run(self, func, *args, **kwargs):
        """安全执行函数"""
        if not self._is_running:
            return None
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(str(e))
            self.error.emit(str(e))
            return None
        finally:
            self.finished.emit()


class DNSUpdateThread(BaseThread):
    """DNS更新线程"""
    error = Signal(str)  # 错误信号

    def __init__(self, platform, ipv4, ipv6):
        super().__init__()
        self.platform = platform
        self.ipv4 = ipv4
        self.ipv6 = ipv6

    def run(self):
        """执行DNS记录更新"""
        try:
            # 先获取当前记录
            current_ipv4, current_ipv6 = self.platform.get_current_records()
            platform_key = self.platform.get_platform_key()
            record_type = self.platform.record_type

            # 根据记录类型选择要更新的IP
            current_ip = current_ipv4 if record_type == 'A' else current_ipv6
            new_ip = self.ipv4 if record_type == 'A' else self.ipv6

            # 记录当前状态
            self.logger.info(f"{platform_key} [{record_type}] - 当前记录: {current_ip or '无'}, 本地IP: {new_ip}")

            # 检查是否需要更新
            if new_ip and current_ip != new_ip:
                # 需要更新时才调用 update_records
                if not self.platform.update_records(self.ipv4, self.ipv6):
                    self.error.emit("更新失败")
            else:
                self.logger.info(f"{platform_key} - 记录已是最新")

        except Exception as e:
            platform_key = self.platform.get_platform_key()
            self.logger.error(f"{platform_key} - 更新失败: {str(e)}")
            self.error.emit(str(e))


class DNSInitThread(BaseThread):
    """DNS平台初始化线程"""
    init_finished = Signal(dict)  # 初始化完成的平台字典

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.platforms = {}

    def run(self):
        import importlib
        config_data = self.config.load_config()
        platforms = config_data.get('platforms', {})

        for platform_name, platform_configs in platforms.items():
            try:
                # 确保 platform_configs 是列表
                if not isinstance(platform_configs, list):
                    platform_configs = [platform_configs]

                # 加载平台类
                module = importlib.import_module(f"dns_platforms.{platform_name}")
                platform_class = getattr(module, f"{platform_name.title()}DNS")

                # 处理每个配置
                for config in platform_configs:
                    try:
                        # 获取完整域名
                        hostname = config.get('hostname', '@')
                        domain = config.get('domain', 'unknown')
                        full_domain = f"{hostname}.{domain}" if hostname != '@' else domain

                        # 构建唯一的平台键
                        platform_key = f"{platform_name}_{full_domain}_{config.get('record_type', 'A')}"

                        # 初始化平台实例
                        self.platforms[platform_key] = platform_class(config)
                        self.logger.info(f"DNS平台初始化成功: [{platform_name.upper()}][{full_domain}]")
                    except Exception as e:
                        self.logger.error(f"初始化DNS记录失败: [{platform_name}][{full_domain}] - {str(e)}")

            except Exception as e:
                self.logger.error(f"加载DNS平台模块失败: {platform_name} - {str(e)}")

        self.init_finished.emit(self.platforms)


class IPCheckThread(BaseThread):
    """IP检查线程"""
    ip_checked = Signal(str, str)  # IPv4, IPv6

    def __init__(self, ip_checker):
        super().__init__()
        self.ip_checker = ip_checker

    def run(self):
        ipv4, ipv6 = self.safe_run(self.ip_checker.get_current_ips)
        self.ip_checked.emit(ipv4 or '', ipv6 or '')


class ThreadManager:
    """线程管理器"""
    _instance = None
    _pool = ThreadPoolExecutor(max_workers=5)  # 限制最大线程数
    _active_threads = set()  # 活动线程集合

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ThreadManager()
        return cls._instance

    def submit_thread(self, thread):
        """提交线程到线程池"""
        self._active_threads.add(thread)
        thread.finished.connect(lambda: self._on_thread_finished(thread))
        return self._pool.submit(thread.run)

    def _on_thread_finished(self, thread):
        """线程完成时的处理"""
        if thread in self._active_threads:
            self._active_threads.remove(thread)

    def stop_all(self):
        """停止所有线程"""
        for thread in list(self._active_threads):
            thread.stop()
        self._pool.shutdown(wait=True)
