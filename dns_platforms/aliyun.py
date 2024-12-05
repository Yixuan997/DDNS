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
        super().__init__(config)
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
        """获取当前DNS记录"""
        try:
            if not self.client:
                self.logger.error("阿里云DNS客户端未初始化")
                return None, None

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
            self.logger.error(f"获取记录失败: {str(e)}")
            return None, None

    def _update_record(self, value):
        """更新记录"""
        try:
            if not self.client:
                self.logger.error("阿里云DNS客户端未初始化")
                return False

            request = alidns_models.DescribeDomainRecordsRequest(
                domain_name=self.domain,
                rrkey_word=self.hostname,
                type=self.record_type
            )

            response = self.client.describe_domain_records(request)
            records = response.body.domain_records.record

            # 如果找到记录就更新，否则创建新记录
            if records:
                for record in records:
                    if record.type == self.record_type and record.rr == self.hostname:
                        try:
                            update_request = alidns_models.UpdateDomainRecordRequest(
                                record_id=record.record_id,
                                rr=self.hostname,
                                type=self.record_type,
                                value=value
                            )
                            self.client.update_domain_record(update_request)
                            self.logger.info(f"[ALIYUN][{self.domain}] - 记录更新成功")
                            return True
                        except Exception as e:
                            self.logger.error(f"更新记录失败: {str(e)}")
                            return False

            # 创建新记录
            try:
                add_request = alidns_models.AddDomainRecordRequest(
                    domain_name=self.domain,
                    rr=self.hostname,
                    type=self.record_type,
                    value=value
                )
                self.client.add_domain_record(add_request)
                self.logger.info(f"[ALIYUN][{self.domain}] - 新记录创建成功")
                return True
            except Exception as e:
                self.logger.error(f"创建记录失败: {str(e)}")
                return False

        except Exception as e:
            self.logger.error(f"更新记录失败: {str(e)}")
            return False

    def clear_cache(self):
        """清除缓存（如果有的话）"""
        pass

    def update_records(self, ipv4, ipv6):
        """更新DNS记录"""
        try:
            # 先获取当前记录
            current_ipv4, current_ipv6 = self.get_current_records()

            # 根据记录类型检查是否需要更新
            if self.record_type == 'A':
                if not ipv4:
                    self.logger.warning(f"[ALIYUN][{self.domain}] - 未提供IPv4地址")
                    return False
                if current_ipv4 == ipv4:
                    self.logger.info(f"[ALIYUN][{self.domain}] - IPv4记录已是最新 ({ipv4})")
                    return True  # 记录已是最新，直接返回True，不显示更新成功
                return self._update_record(ipv4)

            elif self.record_type == 'AAAA':
                if not ipv6:
                    self.logger.warning(f"[ALIYUN][{self.domain}] - 未提供IPv6地址")
                    return False
                if current_ipv6 == ipv6:
                    self.logger.info(f"[ALIYUN][{self.domain}] - IPv6记录已是最新 ({ipv6})")
                    return True  # 记录已是最新，直接返回True，不显示更新成功
                return self._update_record(ipv6)

            return False

        except Exception as e:
            self.logger.error(f"更新记录失败: {str(e)}")
            return False