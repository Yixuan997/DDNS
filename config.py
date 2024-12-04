import json
import os

from utils.logger import Logger


class Config:
    def __init__(self):
        self.config_file = "config.json"  # 配置文件路径在根目录
        self.logger = Logger()

        self.default_config = {
            "platforms": {},  # DNS平台配置
            "settings": {
                "update_interval": 300,  # 默认5分钟更新一次
                "startup": False  # 默认不开机启动
            }
        }

        # 确保配置文件存在
        if not os.path.exists(self.config_file):
            self.save_config(self.default_config)

    def load_config(self):
        """加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            return self.default_config

    def save_config(self, config):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存配置失败: {str(e)}")

    def get_update_interval(self):
        """获取更新间隔（秒）"""
        config = self.load_config()
        return config.get('settings', {}).get('update_interval', 300)

    def save_settings(self, settings):
        """保存设置"""
        config = self.load_config()
        config['settings'] = {
            'update_interval': settings.get('interval', 5) * 60,  # 转换为秒
            'startup': settings.get('startup', False)
        }
        self.save_config(config)

    def get_settings(self):
        """获取设置"""
        config = self.load_config()
        settings = config.get('settings', {})
        return {
            'interval': settings.get('update_interval', 300) // 60,  # 转换为分钟
            'startup': settings.get('startup', False)
        }

    def save_platform_config(self, platform_name, config_data):
        """保存平台配置"""
        config = self.load_config()

        # 确保platforms字段存在
        if 'platforms' not in config:
            config['platforms'] = {}

        # 更新平台配置
        config['platforms'][platform_name] = config_data

        # 保存配置
        self.save_config(config)
        self.logger.info(f"已保存平台配置: [{platform_name.upper()}][{config_data.get('domain', 'unknown')}]")

    def get_platform_config(self, platform_name):
        """获取平台配置"""
        config = self.load_config()
        return config.get('platforms', {}).get(platform_name, {})

    def save_dns_config(self, dns_config):
        """保存DNS配置"""
        config = self.load_config()

        # 新格式直接保存
        if 'platforms' in dns_config:
            config['platforms'] = dns_config['platforms']
        else:
            # 兼容旧格式
            platform_name = dns_config.get('platform', '').lower().replace(' ', '_')
            domain = dns_config.get('domain', '')

            if not platform_name or not domain:
                self.logger.warning("保存DNS配置失败：缺少平台名称或域名")
                return

            if 'platforms' not in config:
                config['platforms'] = {}

            # 保存平台配置
            if platform_name not in config['platforms']:
                config['platforms'][platform_name] = []

            # 如果不是列表，转换为列表
            if not isinstance(config['platforms'][platform_name], list):
                config['platforms'][platform_name] = [config['platforms'][platform_name]]

            # 创建新的记录配置
            record_config = {
                'domain': domain,
                'hostname': dns_config.get('hostname', '@'),
                'record_type': dns_config.get('record_type', 'A')
            }

            # 根据平台类型添加认证信息
            if platform_name == 'cloudflare':
                record_config['api_token'] = dns_config.get('api_token', '')
            elif platform_name == 'tencent':
                record_config['secret_id'] = dns_config.get('secret_id', '')
                record_config['secret_key'] = dns_config.get('secret_key', '')

            # 更新或添加记录
            found = False
            for i, record in enumerate(config['platforms'][platform_name]):
                if (record.get('domain') == domain and
                        record.get('hostname', '@') == record_config.get('hostname', '@')):
                    config['platforms'][platform_name][i] = record_config
                    found = True
                    break

            if not found:
                config['platforms'][platform_name].append(record_config)

        # 保存配置
        self.save_config(config)
