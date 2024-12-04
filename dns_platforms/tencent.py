from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.teo.v20220901 import teo_client, models

from utils.logger import Logger


class TencentDNS:
    # 定义平台配置要求
    CONFIG_FIELDS = {
        'secret_id': {
            'label': 'SecretId',
            'placeholder': '腾讯云SecretId'
        },
        'secret_key': {
            'label': 'SecretKey',
            'placeholder': '腾讯云SecretKey'
        },
        'hostname': {
            'label': '主机名',
            'placeholder': '@ 表示根域名，或输入子域名如 www'
        },
        'domain': {
            'label': '域名',
            'placeholder': '例如：example.com'
        }
    }

    def __init__(self, config):
        """初始化腾讯云DNS
        config: {
            'domain': 'example.com',
            'secret_id': 'SecretId',
            'secret_key': 'SecretKey'
        }
        """
        self.config = config
        self.logger = Logger()
        self.client = None
        self._init_client()

    def _init_client(self):
        """初始化API客户端"""
        try:
            # 实例化一个认证对象
            cred = credential.Credential(
                self.config.get('secret_id'),
                self.config.get('secret_key')
            )

            # 实例化要请求产品的client对象
            self.client = teo_client.TeoClient(cred, "ap-guangzhou")

        except TencentCloudSDKException as e:
            self.logger.error(f"腾讯云DNS客户端初始化失败: {str(e)}")

    def update_records(self, ipv4, ipv6):
        """更新DNS记录"""
        if not self.client:
            self.logger.error("腾讯云DNS客户端未初始化")
            return

        try:
            # 先获取记录列表
            list_request = models.AccelerationDomain()
            list_request.Domain = self.config.get('domain')
            list_response = self.client.DescribeRecordList(list_request)

            # 更新记录
            for record in list_response.RecordList:
                if record.Type == "A" and ipv4:
                    self._update_record(record.RecordId, "A", ipv4)
                elif record.Type == "AAAA" and ipv6:
                    self._update_record(record.RecordId, "AAAA", ipv6)

        except TencentCloudSDKException as e:
            self.logger.error(f"腾讯云DNS记录更新失败: {str(e)}")

    def _update_record(self, record_id, record_type, value):
        """更新单条记录"""
        try:
            # 实例化一个请求对象
            request = models.ModifyRecordRequest()

            # 设置请求参数
            request.Domain = self.config.get('domain')
            request.RecordId = record_id
            request.RecordType = record_type
            request.Value = value
            request.RecordLine = "默认"

            # 发起请求
            response = self.client.ModifyRecord(request)

            self.logger.info(f"腾讯云DNS记录更新成功: {record_type} -> {value}")

        except TencentCloudSDKException as e:
            self.logger.error(f"腾讯云DNS记录更新失败: {str(e)}")

    def get_domains(self):
        """获取域名列表"""
        try:
            # 实例化一个请求对象
            request = models.DescribeDomainListRequest()

            # 发起请求
            response = self.client.DescribeDomainList(request)

            # 返回域名列表
            return [domain.Name for domain in response.DomainList]

        except TencentCloudSDKException as e:
            self.logger.error(f"获取腾讯云域名列表失败: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"获取腾讯云域名列表失败: {str(e)}")
            return []

    def get_record_ips(self):
        """获取当前DNS记录的IP地址"""
        if not self.client:
            self.logger.error("腾讯云DNS客户端未初始化")
            return None, None

        try:
            # 获取记录列表
            list_request = models.DescribeRecordListRequest()
            list_request.Domain = self.config.get('domain')
            list_response = self.client.DescribeRecordList(list_request)

            ipv4 = None
            ipv6 = None

            # 遍历记录找到A和AAAA记录
            for record in list_response.RecordList:
                if record.Type == "A":
                    ipv4 = record.Value
                elif record.Type == "AAAA":
                    ipv6 = record.Value

            return ipv4, ipv6

        except TencentCloudSDKException as e:
            self.logger.error(f"获取腾讯云DNS记录IP失败: {str(e)}")
            return None, None
