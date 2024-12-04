"""
@Project ：DDNS
@File    ：base.py
@IDE     ：PyCharm
@Author  ：杨逸轩
@Date    ：2023/12/02
"""

from abc import ABC, abstractmethod
from utils.logger import Logger


class BaseDNS(ABC):
    """DNS平台基类，所有具体的DNS平台实现都应该继承此类"""

    def __init__(self, config):
        """
        初始化DNS平台
        Args:
            config (dict): 平台配置信息，包含域名、主机名等
        """
        self.config = config
        self.domain = config.get('domain')
        self.hostname = config.get('hostname', '@')
        self.record_type = config.get('record_type', 'A')
        self.logger = Logger()

    @abstractmethod
    def get_current_records(self):
        """
        获取当前DNS记录的IP地址
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

    def get_platform_key(self):
        """
        获取平台标识
        Returns:
            str: 格式为 [平台名][域名] 的标识字符串
        """
        platform_name = self.__class__.__name__.replace('DNS', '').upper()
        return f"[{platform_name}][{self.domain}]"
