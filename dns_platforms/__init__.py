"""
@Project ：DDNS 
@File    ：__init__.py
@IDE     ：PyCharm 
@Author  ：杨逸轩
@Date    ：2024/11/30 23:49 
"""
from .aliyun import AliyunDNS
# 导出所有平台类
from .cloudflare import CloudflareDNS
from .tencent import TencentDNS

# 平台名称到模块的映射
PLATFORM_MAPPING = {
    'Cloudflare': 'cloudflare',
    '腾讯云': 'tencent'
    , '阿里云': 'aliyun'
}

# 平台显示名称列表
PLATFORM_NAMES = list(PLATFORM_MAPPING.keys())

__all__ = ['CloudflareDNS', 'TencentDNS', 'AliyunDNS', 'PLATFORM_MAPPING', 'PLATFORM_NAMES']
