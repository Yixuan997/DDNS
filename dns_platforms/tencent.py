"""
@Project ：DDNS
@File    ：tencent.py
@IDE     ：PyCharm
@Author  ：杨逸轩
@Date    ：2023/12/02
"""

import json

from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.teo.v20220901 import teo_client, models

from .base import BaseDNS


class TencentDNS(BaseDNS):
    """腾讯云DNS平台实现"""

    CONFIG_FIELDS = {
        'hostname': {
            'label': '主机名',
            'placeholder': '@ 表示根域名，或输入子域名如 www'
        },
        'domain': {
            'label': '域名',
            'placeholder': '例如：example.com'
        },
        'secret_id': {
            'label': 'SecretId',
            'placeholder': '腾讯云SecretId'
        },
        'secret_key': {
            'label': 'SecretKey',
            'placeholder': '腾讯云SecretKey'
        }
    }

    def __init__(self, config):
        """
        初始化腾讯云DNS
        Args:
            config: 包含认证信息的配置字典
        """
        super().__init__(config)
        self.client = None
        self._zone_ids = {}  # 用于缓存域名和zone_id的映射
        self._init_client()
        # 初始化时获取一次域名列表
        if self.client:
            self.get_domains()

    def _init_client(self):
        """初始化API客户端"""
        try:
            # 实例化认证对象
            cred = credential.Credential(
                self.config.get('secret_id'),
                self.config.get('secret_key')
            )

            # 实例化http选项
            http_profile = HttpProfile()
            http_profile.endpoint = "teo.tencentcloudapi.com"

            # 实例化client选项
            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile

            # 实例化要请求产品的client对象
            self.client = teo_client.TeoClient(cred, "", client_profile)

        except TencentCloudSDKException as e:
            self.logger.error(f"腾讯云DNS客户端初始化失败: {str(e)}")

    def _cache_zone_id(self, zone_name, zone_id):
        """缓存域名和zone_id的映射关系"""
        self._zone_ids[zone_name] = zone_id

    def get_zone_id(self, domain):
        """获取域名对应的zone_id"""
        return self._zone_ids.get(domain)

    def get_domains(self):
        """获取域名列表"""
        try:
            req = models.DescribeZonesRequest()
            params = {}
            req.from_json_string(json.dumps(params))

            response = self.client.DescribeZones(req)
            zones = json.loads(response.to_json_string())

            domains = []
            if 'Zones' in zones:
                for zone in zones['Zones']:
                    # 只要ActiveStatus是active就认为域名可用
                    if zone.get('ActiveStatus') == 'active':
                        domain = zone['ZoneName']
                        zone_id = zone['ZoneId']
                        domains.append(domain)
                        self._cache_zone_id(domain, zone_id)

            return domains

        except TencentCloudSDKException as e:
            self.logger.error(f"获取域名列表失败: {str(e)}")
            return []

    def get_current_records(self):
        """获取当前DNS记录"""
        try:
            zone_id = self.get_zone_id(self.domain)
            if not zone_id:
                self.logger.error(f"未找到域名 {self.domain} 的ZoneId")
                return None, None

            req = models.DescribeAccelerationDomainsRequest()
            params = {
                "ZoneId": zone_id,
                "Filters": [
                    {
                        "Name": "origin-type",
                        "Values": ["IP_DOMAIN"],
                        "Fuzzy": True
                    }
                ],
                "Direction": "desc",
                "Order": "created_on",
                "Match": "all"
            }
            req.from_json_string(json.dumps(params))

            response = self.client.DescribeAccelerationDomains(req)
            result = json.loads(response.to_json_string())

            ipv4 = None
            ipv6 = None

            if 'AccelerationDomains' in result:
                for domain in result['AccelerationDomains']:
                    domain_name = domain.get('DomainName', '')
                    target_domain = f"{self.hostname}.{self.domain}" if self.hostname != '@' else self.domain

                    if domain_name == target_domain:
                        origin_detail = domain.get('OriginDetail', {})
                        if origin_detail.get('OriginType') == 'IP_DOMAIN':
                            origin = origin_detail.get('Origin')
                            # 根据IP格式判断是IPv4还是IPv6
                            if ':' in origin:  # IPv6包含冒号
                                ipv6 = origin
                            else:  # IPv4
                                ipv4 = origin
                        break

            return ipv4, ipv6

        except TencentCloudSDKException as e:
            self.logger.error(f"获取记录失败: {str(e)}")
            return None, None

    def _update_record(self, value):
        """更新记录"""
        try:
            zone_id = self.get_zone_id(self.domain)
            if not zone_id:
                self.logger.error(f"未找到域名 {self.domain} 的ZoneId")
                return False

            # 构建源站信息
            origin_info = {
                "OriginType": "IP_DOMAIN",
                "Origin": value
            }

            req = models.ModifyAccelerationDomainRequest()
            params = {
                "ZoneId": zone_id,
                "DomainName": f"{self.hostname}.{self.domain}" if self.hostname != '@' else self.domain,
                "OriginInfo": origin_info
            }
            req.from_json_string(json.dumps(params))

            response = self.client.ModifyAccelerationDomain(req)
            result = json.loads(response.to_json_string())

            success = 'Response' in result and 'RequestId' in result['Response']
            if success:
                self.logger.info(f"[TENCENT][{self.domain}] - 记录更新成功")
            return success

        except TencentCloudSDKException as e:
            self.logger.error(f"更新记录失败: {str(e)}")
            return False
