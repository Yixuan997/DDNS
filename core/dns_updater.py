import importlib

from utils.logger import Logger


class DNSUpdater:
    def __init__(self, config):
        self.config = config
        self.logger = Logger()
        self.logger.info("初始化DNS更新器...")
        self.logger.info(f"开始初始化 1 个DNS平台")
        self.platforms = self._init_platforms()

    def _get_platform_class(self, platform_name):
        """动态获取DNS平台类"""
        try:
            # 将平台名称转换为类名格式 (例如: cloudflare -> CloudflareDNS)
            class_name = f"{platform_name.title()}DNS"
            module = importlib.import_module(f"dns_platforms.{platform_name}")
            return getattr(module, class_name)
        except Exception as e:
            self.logger.error(f"加载DNS平台模块失败: {platform_name} - {str(e)}")
            return None

    def _init_platforms(self):
        """初始化所有配置的DNS平台"""
        platforms = {}
        platform_configs = self.config.get_platform_configs()

        for platform_name, records in platform_configs.items():
            platform_class = self._get_platform_class(platform_name)
            if not platform_class:
                continue

            for record in records:
                # 检查必要的配置是否完整
                required_fields = ['domain']  # 基本必需字段
                if hasattr(platform_class, 'CONFIG_FIELDS'):
                    required_fields.extend(platform_class.CONFIG_FIELDS.keys())

                # 检查所有必需字段是否存在且不为空
                if not all(k in record and record[k] for k in required_fields):
                    continue

                try:
                    platform = platform_class(record)
                    platform_key = f"{platform_name}_{record.get('domain')}_{record.get('record_type', 'A')}"
                    platforms[platform_key] = platform
                    self.logger.info(f"DNS平台初始化成功: {platform_key}")
                except Exception as e:
                    self.logger.debug(f"DNS平台初始化失败: {platform_name} - {str(e)}")  # 改为debug级别

        return platforms

    def update_records(self, ipv4, ipv6):
        """更新所有平台的DNS记录"""
        if not self.platforms:
            self.logger.warning("没有配置任何DNS平台")
            return

        for platform_key, platform in self.platforms.items():
            try:
                # 先获取当前记录
                try:
                    current_ipv4, current_ipv6 = platform.get_current_records()
                except Exception as e:
                    self.logger.error(f"获取当前记录失败: {str(e)}")
                    continue

                # 检查是否需要更新
                need_update = False
                if platform.record_type == 'A':
                    if not ipv4:
                        continue
                    if current_ipv4 == ipv4:
                        self.logger.info(f"[{platform_key}] DNS记录已是最新 ({ipv4})")
                    else:
                        need_update = True
                        self.logger.info(f"[{platform_key}] DNS记录需要更新: IPv4: {current_ipv4} -> {ipv4}")
                elif platform.record_type == 'AAAA':
                    if not ipv6:
                        continue
                    if current_ipv6 == ipv6:
                        self.logger.info(f"[{platform_key}] DNS记录已是最新 ({ipv6})")
                    else:
                        need_update = True
                        self.logger.info(f"[{platform_key}] DNS记录需要更新: IPv6: {current_ipv6} -> {ipv6}")
                else:
                    continue

                # 只在需要更新时执行更新
                if need_update:
                    try:
                        if platform.update_records(ipv4, ipv6):
                            self.logger.info(f"[{platform_key}] DNS记录更新成功")
                            if hasattr(self, 'main_window') and self.main_window:
                                self.main_window.show_message(f"DNS记录更新成功: {platform_key}", "success")
                        else:
                            self.logger.error(f"[{platform_key}] DNS记录更新失败")
                            if hasattr(self, 'main_window') and self.main_window:
                                self.main_window.show_message(f"DNS记录更新失败: {platform_key}", "error")
                    except Exception as e:
                        self.logger.error(f"[{platform_key}] 更新记录时出错: {str(e)}")
                        if hasattr(self, 'main_window') and self.main_window:
                            self.main_window.show_message(f"更新记录出错: {platform_key}", "error")

            except Exception as e:
                self.logger.error(f"[{platform_key}] 检查和更新DNS记录失败: {str(e)}")
                if hasattr(self, 'main_window') and self.main_window:
                    self.main_window.show_message(f"DNS记录更新出错: {platform_key}", "error")
