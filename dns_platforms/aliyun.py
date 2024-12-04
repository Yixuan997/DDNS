"""
@Project ：DDNS 
@File    ：aliyun.py
@IDE     ：PyCharm 
@Author  ：杨逸轩
@Date    ：2023/12/02
"""

from alibabacloud_alidns20150109.client import Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_alidns20150109 import models as alidns_models

from .base import BaseDNS


class AliyunDNS(BaseDNS):
    """阿里云DNS平台实现"""

    CONFIG_FIELDS = {
        'hostname': {
            'label': '主机名',
            'placeholder': '@ 表示根域名，或输入子域名如 www'
        },
        'domain': {
            'label': '域名',
            'placeholder': '例如: example.com'
        },
        'access_key_id': {
            'label': 'AccessKey ID',
            'placeholder': '从阿里云获取的 AccessKey ID'
        },
        'access_key_secret': {
            'label': 'AccessKey Secret',
            'placeholder': '从阿里云获取的 AccessKey Secret'
        }
    }

    def __init__(self, config):
        """
        初始化阿里云DNS客户端
        Args:
            config: 包含AccessKey等配置信息的字典
        """
        BaseDNS.__init__(self, config)
        self.client = self._create_client()

    def _create_client(self):
        """
        创建阿里云DNS客户端
        Returns:
            Client: 阿里云DNS客户端实例，失败返回None
        """
        try:
            config = open_api_models.Config(
                access_key_id=self.config.get('access_key_id'),
                access_key_secret=self.config.get('access_key_secret')
            )
            config.endpoint = 'alidns.cn-hangzhou.aliyuncs.com'
            return Client(config)
        except Exception as e:
            self.logger.error(f"创建阿里云DNS客户端失败: {str(e)}")
            return None

    def get_domains(self):
        """
        获取可用域名列表
        Returns:
            list: 域名列表
        """
        try:
            request = alidns_models.DescribeDomainsRequest()
            response = self.client.describe_domains(request)
            domains = response.body.domains.domain
            return [domain.domain_name for domain in domains]
        except Exception as e:
            self.logger.error(f"获取域名列表失败: {str(e)}")
            return []

    def get_current_records(self):
        """
        获取当前记录值
        Returns:
            tuple: (ipv4, ipv6) 当前记录的IP地址
        """
        try:
            request = alidns_models.DescribeDomainRecordsRequest(
                domain_name=self.domain,
                rrkey_word=self.hostname,
                type=self.record_type
            )
            response = self.client.describe_domain_records(request)
            records = response.body.domain_records.record

            ipv4 = None
            ipv6 = None

            for record in records:
                if record.type == 'A' and record.rr == self.hostname:
                    ipv4 = record.value
                elif record.type == 'AAAA' and record.rr == self.hostname:
                    ipv6 = record.value

            return ipv4, ipv6

        except Exception as e:
            self.logger.error(f"获取阿里云DNS记录失败: {str(e)}")
            return None, None

    def update_records(self, ipv4, ipv6):
        """更新DNS记录"""
        try:
            # 根据记录类型选择要更新的IP
            if self.record_type == 'A' and not ipv4:
                raise ValueError("未提供IPv4地址")
            if self.record_type == 'AAAA' and not ipv6:
                raise ValueError("未提供IPv6地址")

            # 获取当前记录
            records = self.client.describe_domain_records(
                alidns_models.DescribeDomainRecordsRequest(
                    domain_name=self.domain,
                    rrkey_word=self.hostname,
                    type=self.record_type
                )
            ).body.domain_records.record

            # 准备更新数据
            new_value = ipv4 if self.record_type == 'A' else ipv6

            # 尝试更新现有记录
            for record in records:
                if record.type == self.record_type and record.rr == self.hostname:
                    if record.value != new_value:
                        request = alidns_models.UpdateDomainRecordRequest(
                            record_id=record.record_id,
                            rr=self.hostname,
                            type=self.record_type,
                            value=new_value
                        )
                        self.client.update_domain_record(request)
                        self.logger.info(f"[ALIYUN][{self.domain}] - 记录更新成功")
                    return True

            # 如果没有找到记录，创建新记录
            if not records:
                request = alidns_models.AddDomainRecordRequest(
                    domain_name=self.domain,
                    rr=self.hostname,
                    type=self.record_type,
                    value=new_value
                )
                self.client.add_domain_record(request)
                self.logger.info(f"[ALIYUN][{self.domain}] - 新记录创建成功")
                return True

            return True  # 如果记录存在但不需要更新

        except Exception as e:
            self.logger.error(f"更新阿里云DNS记录失败: {str(e)}")
            raise  # 重新抛出异常，让上层处理

    def clear_cache(self):
        """清除缓存（如果有的话）"""
        pass