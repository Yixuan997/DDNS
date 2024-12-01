from abc import ABC, abstractmethod

from utils.logger import Logger


class BaseDNS(ABC):
    """DNS平台基类"""

    def __init__(self, config):
        """
        初始化DNS平台
        Args:
            config (dict): 平台配置信息
        """
        self.config = config
        self.logger = Logger()
        self.domain = config.get('domain', '')
        self.hostname = config.get('hostname', '@')

    @abstractmethod
    def get_current_records(self):
        """获取当前DNS记录的IP地址
        Returns:
            tuple: (ipv4, ipv6) DNS记录中的IP地址
        """
        pass

    @abstractmethod
    def update_records(self, ipv4, ipv6):
        """
        更新DNS记录
        Args:
            ipv4 (str): IPv4地址
            ipv6 (str): IPv6地址
        Returns:
            bool: 更新是否成功
        """
        pass

    @abstractmethod
    def get_domains(self):
        """
        获取可用域名列表
        Returns:
            list: 域名列表
        """
        pass
