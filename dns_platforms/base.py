"""
@Project ：DDNS
@File    ：base.py
@IDE     ：PyCharm
@Author  ：杨逸轩
@Date    ：2023/12/02

DNS平台的基类，定义了所有DNS平台必须实现的接口
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

    def update_records(self, ipv4, ipv6):
        """
        更新DNS记录
        Args:
            ipv4: IPv4地址
            ipv6: IPv6地址
        Returns:
            bool: 如果记录已是最新返回 True，如果更新成功也返回 True，更新失败返回 False
        """
        try:
            # 先获取当前记录
            current_ipv4, current_ipv6 = self.get_current_records()

            # 根据记录类型检查是否需要更新
            if self.record_type == 'A':
                if not ipv4:
                    self.logger.warning(f"[{self.__class__.__name__}][{self.domain}] - 未提供IPv4地址")
                    return False
                if current_ipv4 == ipv4:
                    self.logger.info(f"[{self.__class__.__name__}][{self.domain}] - IPv4记录已是最新 ({ipv4})")
                    return True  # 记录已是最新，直接返回True
                success = self._update_record(ipv4)  # 只在需要更新时调用
                if success:
                    self.logger.info(f"[{self.__class__.__name__}][{self.domain}] - 记录更新成功")
                return success

            elif self.record_type == 'AAAA':
                if not ipv6:
                    self.logger.warning(f"[{self.__class__.__name__}][{self.domain}] - 未提供IPv6地址")
                    return False
                if current_ipv6 == ipv6:
                    self.logger.info(f"[{self.__class__.__name__}][{self.domain}] - IPv6记录已是最新 ({ipv6})")
                    return True  # 记录已是最新，直接返回True
                success = self._update_record(ipv6)  # 只在需要更新时调用
                if success:
                    self.logger.info(f"[{self.__class__.__name__}][{self.domain}] - 记录更新成功")
                return success

            return False

        except Exception as e:
            self.logger.error(f"更新记录失败: {str(e)}")
            return False

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
