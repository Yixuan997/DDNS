"""
@Project ：DDNS 
@File    ：threads.py
@IDE     ：PyCharm 
@Author  ：杨逸轩
@Date    ：2023/12/02
"""

from PySide6.QtCore import QThread, Signal

from utils.logger import Logger


class BaseThread(QThread):
    """基础线程类"""
    error = Signal(str)  # 错误信号

    def __init__(self):
        super().__init__()
        self.logger = Logger()

    def safe_run(self, func, *args, **kwargs):
        """
        安全执行函数，捕获并记录异常
        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
        Returns:
            执行结果，异常时返回None
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(str(e))
            self.error.emit(str(e))
            return None


class DNSUpdateThread(BaseThread):
    """DNS更新线程"""
    update_finished = Signal(str, bool)  # 平台标识, 是否成功

    def __init__(self, platform, ipv4, ipv6):
        """
        初始化DNS更新线程
        Args:
            platform: DNS平台实例
            ipv4: IPv4地址
            ipv6: IPv6地址
        """
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
            if record_type == 'A':
                current_ip = current_ipv4
                new_ip = self.ipv4
            else:
                current_ip = current_ipv6
                new_ip = self.ipv6

            # 记录当前状态
            self.logger.info(f"{platform_key} [{record_type}] - 当前记录: {current_ip or '无'}, 本地IP: {new_ip}")

            # 检查是否需要更新
            if new_ip and current_ip != new_ip:
                success = self.platform.update_records(self.ipv4, self.ipv6)
                self.update_finished.emit(platform_key, success)
            else:
                self.logger.info(f"{platform_key} - 记录已是最新")
                self.update_finished.emit(platform_key, True)

        except Exception as e:
            platform_key = self.platform.get_platform_key()
            self.logger.error(f"{platform_key} - 更新失败: {str(e)}")
            self.error.emit(str(e))
            self.update_finished.emit(platform_key, False)


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

        for platform_name, platform_config in platforms.items():
            try:
                if isinstance(platform_config, list):
                    if not platform_config:
                        continue
                    platform_config = platform_config[0]

                module = importlib.import_module(f"dns_platforms.{platform_name}")
                platform_class = getattr(module, f"{platform_name.title()}DNS")
                domain = platform_config.get('domain', 'unknown')
                platform_key = f"[{platform_name.upper()}][{domain}]"
                self.platforms[platform_key] = platform_class(platform_config)

            except Exception as e:
                self.logger.error(f"初始化DNS平台失败: {platform_name}")

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
