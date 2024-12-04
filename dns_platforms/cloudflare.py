"""
@Project ：DDNS
@File    ：cloudflare.py
@IDE     ：PyCharm
@Author  ：杨逸轩
@Date    ：2023/12/02
"""

import requests
from .base import BaseDNS


class CloudflareDNS(BaseDNS):
    """Cloudflare DNS平台实现"""

    API_BASE = "https://api.cloudflare.com/client/v4"

    CONFIG_FIELDS = {
        'hostname': {
            'label': '主机名',
            'placeholder': '@ 表示根域名，或输入子域名如 www'
        },
        'domain': {
            'label': '域名',
            'placeholder': '例如: example.com'
        },
        'api_token': {
            'label': 'API Token',
            'placeholder': '从 Cloudflare 获取的 API Token'
        }
    }

    def __init__(self, config):
        """
        初始化Cloudflare DNS客户端
        Args:
            config: 包含API Token等配置信息的字典
        """
        super().__init__(config)
        self.api_token = config.get('api_token')
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        self._zone_id = None
        self._record_ids = {}

        if self.domain:
            self._zone_id = self._fetch_zone_id()

    def _fetch_zone_id(self):
        """
        从API获取zone_id
        Returns:
            str: zone_id，失败返回None
        """
        try:
            self.logger.debug(f"正在获取域名 {self.domain} 的Zone ID...")
            response = requests.get(
                f"{self.API_BASE}/zones",
                headers=self.headers,
                params={'name': self.domain}
            )
            response.raise_for_status()
            data = response.json()

            if not data['success'] or not data['result']:
                self.logger.error(f"获取Zone ID失败: {data.get('errors', [])}")
                return None

            zone_id = data['result'][0]['id']
            self.logger.debug(f"成功获取Zone ID: {zone_id}")
            return zone_id
        except Exception as e:
            self.logger.error(f"获取Zone ID失败: {str(e)}")
            return None

    def get_zone_id(self):
        """获取缓存的zone_id"""
        return self._zone_id

    def get_record_id(self, zone_id, record_type):
        """获取DNS记录ID（使用缓存）"""
        if record_type in self._record_ids:
            return self._record_ids[record_type]

        try:
            params = {
                'type': record_type,
                'name': f"{self.hostname}.{self.domain}" if self.hostname != '@' else self.domain
            }

            response = requests.get(
                f"{self.API_BASE}/zones/{zone_id}/dns_records",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()

            if data['success'] and data['result']:
                record_id = data['result'][0]['id']
                self._record_ids[record_type] = record_id
                return record_id
            return None
        except Exception as e:
            self.logger.error(f"获取Cloudflare记录ID失败: {str(e)}")
            return None

    def _make_request(self, method, endpoint, **kwargs):
        """通用的API请求处理方法"""
        try:
            url = f"{self.API_BASE}/{endpoint}"
            response = requests.request(
                method,
                url,
                headers=self.headers,
                **kwargs
            )
            response.raise_for_status()
            data = response.json()

            if not data['success']:
                error_msg = data.get('errors', [])
                self.logger.error(f"API请求失败: {error_msg}")
                return None
            return data['result']
        except Exception as e:
            self.logger.error(f"API请求出错: {str(e)}")
            return None

    def get_current_records(self):
        """获取当前DNS记录"""
        zone_id = self.get_zone_id()
        if not zone_id:
            self.logger.error(f"获取Zone ID失败，请检查域名 {self.domain} 是否正确配置")
            return None, None

        ipv4_id = self.get_record_id(zone_id, 'A')
        ipv6_id = self.get_record_id(zone_id, 'AAAA')

        ipv4 = None
        ipv6 = None

        if ipv4_id:
            result = self._make_request('GET', f"zones/{zone_id}/dns_records/{ipv4_id}")
            if result:
                ipv4 = result['content']

        if ipv6_id:
            result = self._make_request('GET', f"zones/{zone_id}/dns_records/{ipv6_id}")
            if result:
                ipv6 = result['content']

        return ipv4, ipv6

    def update_record(self, zone_id, record_id, record_type, ip):
        """更新DNS记录"""
        data = {
            'type': record_type,
            'name': f"{self.hostname}.{self.domain}" if self.hostname != '@' else self.domain,
            'content': ip,
            'proxied': False
        }

        if record_id:
            # 更新现有记录
            result = self._make_request('PUT', f"zones/{zone_id}/dns_records/{record_id}", json=data)
        else:
            # 创建新记录
            result = self._make_request('POST', f"zones/{zone_id}/dns_records", json=data)

        return result is not None

    def update_records(self, ipv4, ipv6):
        """更新所有DNS记录"""
        zone_id = self.get_zone_id()
        if not zone_id:
            self.logger.error("获取Zone ID失败")
            return False

        current_ipv4, current_ipv6 = self.get_current_records()

        if ipv4 and ipv4 != current_ipv4:
            ipv4_id = self.get_record_id(zone_id, 'A')
            self.logger.info(f"[[CLOUDFLARE][{self.domain}]] DNS记录需要更新: IPv4: {current_ipv4} -> {ipv4}")
            if not self.update_record(zone_id, ipv4_id, 'A', ipv4):
                return False

        if ipv6 and ipv6 != current_ipv6:
            ipv6_id = self.get_record_id(zone_id, 'AAAA')
            self.logger.info(f"[[CLOUDFLARE][{self.domain}]] DNS记录需要更新: IPv6: {current_ipv6} -> {ipv6}")
            if not self.update_record(zone_id, ipv6_id, 'AAAA', ipv6):
                return False

        return True

    def get_domains(self):
        """获取可用域名列表"""
        try:
            result = self._make_request('GET', 'zones')
            if result:
                return [zone['name'] for zone in result]
            return []
        except Exception as e:
            self.logger.error(f"获取域名列表失败: {str(e)}")
            return []

    def clear_cache(self):
        """清除所有缓存"""
        self._zone_id = None
        self._record_ids.clear()
