import importlib

from utils.logger import Logger


class DNSUpdater:
    def __init__(self, config, main_window=None):
        self.config = config
        self.main_window = main_window
        self.logger = Logger()
        self.platforms = {}
        self.logger.info("初始化DNS更新器...")
        self._init_platforms()

    def _init_platforms(self):
        """初始化所有配置的DNS平台"""
        config = self.config.load_config()
        platforms = config.get('platforms', {})

        if not platforms:
            self.logger.warning("未配置任何DNS平台")
            return

        self.logger.info(f"开始初始化 {len(platforms)} 个DNS平台")

        for platform_name, platform_config in platforms.items():
            try:
                # 如果配置是列表，取第一个配置
                if isinstance(platform_config, list):
                    if not platform_config:  # 如果列表为空
                        continue
                    platform_config = platform_config[0]

                # 动态加载平台模块
                self.logger.debug(f"正在加载DNS平台模块: {platform_name.upper()}")
                module = importlib.import_module(f"dns_platforms.{platform_name}")
                platform_class = getattr(module, f"{platform_name.title()}DNS")

                # 获取域名
                domain = platform_config.get('domain', 'unknown')

                # 创建平台实例
                platform_key = f"[{platform_name.upper()}][{domain}]"
                self.platforms[platform_key] = platform_class(platform_config)
                self.logger.info(f"DNS平台初始化成功: {platform_key}")
            except Exception as e:
                self.logger.error(f"DNS平台初始化失败: [{platform_name.upper()}] - {str(e)}")

    def check_and_update(self, local_ipv4, local_ipv6):
        """检查并更新DNS记录"""
        update_count = 0

        for platform_name, platform in self.platforms.items():
            try:
                # 获取当前DNS记录的IP
                try:
                    dns_ipv4, dns_ipv6 = platform.get_current_records()
                except Exception as e:
                    self.logger.error(f"获取当前记录失败: {str(e)}")
                    continue

                # 检查是否需要更新
                need_update = False
                update_msg = []

                # 从配置中获取记录类型
                record_type = platform.config.get('record_type', 'A')

                if record_type == 'A' and local_ipv4 and dns_ipv4 != local_ipv4:
                    need_update = True
                    update_msg.append(f"IPv4: {dns_ipv4} -> {local_ipv4}")

                if record_type == 'AAAA' and local_ipv6 and dns_ipv6 != local_ipv6:
                    need_update = True
                    update_msg.append(f"IPv6: {dns_ipv6} -> {local_ipv6}")

                # 只在需要时更新
                if need_update:
                    success = False
                    try:
                        if record_type == 'A':
                            success = platform.update_records(local_ipv4, None)
                        elif record_type == 'AAAA':
                            success = platform.update_records(None, local_ipv6)

                        if success:
                            self.logger.info(f"[{platform_name}] DNS记录更新成功")
                            if self.main_window:
                                self.main_window.show_message(f"DNS记录更新成功: {platform_name}", "success")
                            update_count += 1
                        else:
                            self.logger.error(f"[{platform_name}] DNS记录更新失败")
                            if self.main_window:
                                self.main_window.show_message(f"DNS记录更新失败: {platform_name}", "error")
                    except Exception as e:
                        self.logger.error(f"更新记录时出错: {str(e)}")
                        if self.main_window:
                            self.main_window.show_message(f"更新记录出错: {platform_name}", "error")
                else:
                    self.logger.debug(f"[{platform_name}] DNS记录无需更新")
                    if self.main_window:
                        self.main_window.show_message(f"DNS记录已是最新: {platform_name}", "success")

            except Exception as e:
                self.logger.error(f"[{platform_name}] 检查和更新DNS记录失败: {str(e)}")
                if self.main_window:
                    self.main_window.show_message(f"DNS记录更新出错: {platform_name}", "error")

        return update_count
