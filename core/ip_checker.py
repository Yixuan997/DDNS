import requests

from utils.logger import Logger


class IPChecker:
    def __init__(self):
        self.logger = Logger()
        self.last_ipv4 = None
        self.last_ipv6 = None

        # IP检查服务的URL
        self.ipv4_api = 'https://4.ipw.cn'
        self.ipv6_api = 'https://6.ipw.cn'

        # 请求超时时间（秒）
        self.timeout = 10

    def get_current_ips(self):
        """获取当前的IPv4和IPv6地址"""
        ipv4 = self._get_ip(self.ipv4_api, "IPv4")
        ipv6 = self._get_ip(self.ipv6_api, "IPv6")
        return ipv4, ipv6

    def _get_ip(self, url, ip_type):
        """从指定URL获取IP地址"""
        try:
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                ip = response.text.strip()
                self.logger.debug(f"获取{ip_type}地址成功: {ip}")
                return ip
            else:
                self.logger.warning(f"获取{ip_type}地址失败: HTTP {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            self.logger.error(f"获取{ip_type}地址超时")
            return None
        except requests.exceptions.ConnectionError:
            self.logger.error(f"获取{ip_type}地址失败: 连接错误")
            return None
        except Exception as e:
            self.logger.error(f"获取{ip_type}地址出错: {str(e)}")
            return None

    def is_ip_changed(self, current_ipv4, current_ipv6):
        """检查IP是否发生变化"""
        changed = False

        if current_ipv4 and current_ipv4 != self.last_ipv4:
            changed = True
            self.logger.info(f"IPv4地址已更新: {self.last_ipv4} -> {current_ipv4}")
            self.last_ipv4 = current_ipv4

        if current_ipv6 and current_ipv6 != self.last_ipv6:
            changed = True
            self.logger.info(f"IPv6地址已更新: {self.last_ipv6} -> {current_ipv6}")
            self.last_ipv6 = current_ipv6

        return changed

    def get_last_ips(self):
        """获取上次检查的IP地址"""
        return self.last_ipv4, self.last_ipv6
