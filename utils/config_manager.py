import json
from pathlib import Path


class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / '.ddns_client'
        self.config_file = self.config_dir / 'config.json'
        self.ensure_config_exists()

    def ensure_config_exists(self):
        """确保配置文件存在"""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True)

        if not self.config_file.exists():
            default_config = {
                'update_interval': 300,  # 5分钟
                'startup': False,
                'platforms': {
                    'cloudflare': [{
                        'domain': '',
                        'hostname': '@',  # 添加默认主机名
                        'api_token': ''
                    }],
                    'tencent': [{
                        'domain': '',
                        'hostname': '@',  # 添加默认主机名
                        'secret_id': '',
                        'secret_key': ''
                    }]
                }
            }
            self.save_config(default_config)

    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            # 如果配置文件损坏，返回默认配置
            return {
                'update_interval': 300,
                'startup': False,
                'platforms': {}
            }

    def save_config(self, config):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def get_update_interval(self):
        """获取更新间隔（秒）"""
        config = self.load_config()
        return config.get('update_interval', 300)

    def get_platform_configs(self):
        """获取DNS平台配置"""
        config = self.load_config()
        return config.get('platforms', {})

    def save_dns_config(self, dns_config):
        """保存DNS配置"""
        config = self.load_config()

        # 新格式直接保存
        if 'platforms' in dns_config:
            config['platforms'] = dns_config['platforms']
        # 兼容旧格式
        else:
            platform_name = dns_config['platform'].lower().replace(' ', '_')
            if 'platforms' not in config:
                config['platforms'] = {}
            config['platforms'][platform_name] = {
                'access_key': dns_config['access_key'],
                'secret_key': dns_config['secret_key'],
                'domain': dns_config['domain']
            }

        self.save_config(config)

    def save_settings(self, settings):
        """保存常规设置"""
        config = self.load_config()
        config['update_interval'] = settings['interval'] * 60  # 转换为秒
        config['startup'] = settings['startup']
        self.save_config(config)

    def get_startup_enabled(self):
        """获取开机自启动状态"""
        config = self.load_config()
        return config.get('startup', False)
