import importlib
import time

from utils.logger import Logger


class DNSUpdater:
    def __init__(self, config):
        self.config = config
        self.logger = Logger()
        self.logger.info("初始化DNS更新器...")
        self._stats = {
            'updates': 0,  # 总更新次数
            'successes': 0,  # 成功次数
            'failures': 0,  # 失败次数
            'start_time': time.time(),  # 启动时间
        }
        self.platforms = self._init_platforms()

    def get_stats(self):
        """获取统计信息"""
        uptime = time.time() - self._stats['start_time']
        return {
            **self._stats,
            'uptime': uptime,
            'success_rate': (self._stats['successes'] / self._stats['updates'] * 100) if self._stats[
                                                                                             'updates'] > 0 else 0
        }

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

            # 确保 records 是列表
            if not isinstance(records, list):
                records = [records]

            # 遍历每个记录
            for record in records:
                # 检查必要的配置是否完整
                required_fields = ['domain', 'hostname']  # 基本必需字段
                if hasattr(platform_class, 'CONFIG_FIELDS'):
                    required_fields.extend(platform_class.CONFIG_FIELDS.keys())

                # 检查所有必需字段是否存在且不为空
                if not all(k in record and record[k] for k in required_fields):
                    continue

                try:
                    platform = platform_class(record)
                    # 使用完整域名构建唯一的 key
                    full_domain = f"{record['hostname']}.{record['domain']}" if record['hostname'] != '@' else record[
                        'domain']
                    platform_key = f"{platform_name}_{full_domain}_{record.get('record_type', 'A')}"
                    platforms[platform_key] = platform
                    self.logger.info(f"DNS平台初始化成功: [{platform_name.upper()}][{full_domain}]")
                except Exception as e:
                    self.logger.debug(f"DNS平台初始化失败: {platform_name}_{full_domain} - {str(e)}")

        # 输出初始化的平台数量
        self.logger.info(f"共初始化 {len(platforms)} 个DNS记录")
        return platforms

    def update_records(self, ipv4, ipv6):
        """更新所有平台的DNS记录"""
        start_time = time.time()
        self._stats['updates'] += 1

        if not self.platforms:
            self.logger.warning("没有配置任何DNS平台")
            return

        # 记录开始更新
        self.logger.info(f"开始更新 {len(self.platforms)} 个DNS记录")

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
                record_type = platform.record_type
                current_ip = current_ipv4 if record_type == 'A' else current_ipv6
                new_ip = ipv4 if record_type == 'A' else ipv6

                if not new_ip:
                    continue

                # 获取完整域名用于日志
                full_domain = f"{platform.hostname}.{platform.domain}" if platform.hostname != '@' else platform.domain
                platform_name = platform.__class__.__name__.replace('DNS', '').upper()
                log_key = f"[{platform_name}][{full_domain}]"

                if current_ip == new_ip:
                    self.logger.info(f"{log_key} - 记录已是最新")
                else:
                    need_update = True
                    self.logger.info(f"{log_key} DNS记录需要更新: {record_type}: {current_ip} -> {new_ip}")

                # 只在需要更新时执行更新
                if need_update:
                    success = platform.update_records(ipv4, ipv6)
                    if success:
                        self._stats['successes'] += 1
                    else:
                        self._stats['failures'] += 1

            except Exception as e:
                self._stats['failures'] += 1
                self.logger.error(f"[{platform_key}] 检查和更新DNS记录失败: {str(e)}")

        # 记录性能指标
        elapsed = time.time() - start_time
        self.logger.debug(f"DNS更新耗时: {elapsed:.2f}秒")
