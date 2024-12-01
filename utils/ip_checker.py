import requests

from utils.logger import Logger


class IPChecker:
    def __init__(self):
        self.ipv4 = None
        self.ipv6 = None
        self.ipv4_api = "https://4.ipw.cn/"
        self.ipv6_api = "https://6.ipw.cn/"
        self.logger = Logger()

    def get_current_ips(self):
        """获取当前的IPv4和IPv6地址"""
        self.logger.info("开始获取IP地址...")

        try:
            ipv4_response = requests.get(self.ipv4_api, timeout=5)
            self.ipv4 = ipv4_response.text if ipv4_response.status_code == 200 else None
            if self.ipv4:
                self.logger.info(f"获取到IPv4地址: {self.ipv4}")
            else:
                self.logger.warning("未能获取IPv4地址")
        except Exception as e:
            self.logger.error(f"获取IPv4地址失败: {str(e)}")
            self.ipv4 = None

        try:
            ipv6_response = requests.get(self.ipv6_api, timeout=5)
            self.ipv6 = ipv6_response.text if ipv6_response.status_code == 200 else None
            if self.ipv6:
                self.logger.info(f"获取到IPv6地址: {self.ipv6}")
            else:
                self.logger.warning("未能获取IPv6地址")
        except Exception as e:
            self.logger.error(f"获取IPv6地址失败: {str(e)}")
            self.ipv6 = None

        return self.ipv4, self.ipv6

    def is_ip_changed(self, new_ipv4, new_ipv6):
        """检查IP是否发生变化"""
        changed = False
        if new_ipv4 != self.ipv4:
            self.logger.info(f"IPv4地址发生变化: {self.ipv4} -> {new_ipv4}")
            self.ipv4 = new_ipv4
            changed = True
        if new_ipv6 != self.ipv6:
            self.logger.info(f"IPv6地址发生变化: {self.ipv6} -> {new_ipv6}")
            self.ipv6 = new_ipv6
            changed = True

        if not changed:
            self.logger.debug("IP地址未发生变化")

        return changed

    def check(self):
        """检查IP地址"""
        # ... 实现IP检查逻辑 ...
        pass
