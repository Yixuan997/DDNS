"""
@Project ：DDNS
@File    ：ip_checker.py
@IDE     ：PyCharm
@Author  ：杨逸轩
@Date    ：2023/12/02
"""

import requests
from utils.logger import Logger


class IPChecker:
    """IP地址检查器，负责获取当前主机的公网IPv4和IPv6地址"""

    def __init__(self):
        """初始化IP检查器"""
        self.logger = Logger()
        self._last_ipv4 = None
        self._last_ipv6 = None
        self.ipv4_api = "https://4.ipw.cn/"
        self.ipv6_api = "https://6.ipw.cn/"

    def _get_ipv4(self):
        """
        获取IPv4地址
        Returns:
            str: IPv4地址，失败返回None
        """
        try:
            response = requests.get(self.ipv4_api, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
            return None
        except Exception:
            return None

    def _get_ipv6(self):
        """
        获取IPv6地址
        Returns:
            str: IPv6地址，失败返回None
        """
        try:
            response = requests.get(self.ipv6_api, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
            return None
        except Exception:
            return None

    def get_current_ips(self):
        """获取当前的IPv4和IPv6地址"""
        try:
            ipv4 = self._get_ipv4()
            ipv6 = self._get_ipv6()

            # 只在IP变化时输出日志
            if ipv4 != self._last_ipv4 or ipv6 != self._last_ipv6:
                if ipv4 != self._last_ipv4:
                    self.logger.info(f"IPv4地址: {ipv4 or '无'}")
                if ipv6 != self._last_ipv6:
                    self.logger.info(f"IPv6地址: {ipv6 or '无'}")

                self._last_ipv4 = ipv4
                self._last_ipv6 = ipv6

            return ipv4, ipv6

        except Exception as e:
            self.logger.error(f"获取IP地址失败: {str(e)}")
            return None, None

    def is_ip_changed(self, new_ipv4, new_ipv6):
        """检查IP是否发生变化"""
        changed = False
        if new_ipv4 != self._last_ipv4:
            self.logger.info(f"IPv4地址发生变化: {self._last_ipv4} -> {new_ipv4}")
            self._last_ipv4 = new_ipv4
            changed = True
        if new_ipv6 != self._last_ipv6:
            self.logger.info(f"IPv6地址发生变化: {self._last_ipv6} -> {new_ipv6}")
            self._last_ipv6 = new_ipv6
            changed = True

        if not changed:
            self.logger.debug("IP地址未发生变化")

        return changed

    def check(self):
        """检查IP地址"""
        # ... 实现IP检查逻辑 ...
        pass
