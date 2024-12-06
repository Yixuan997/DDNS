"""
@Project ：DDNS
@File    ：dns_updater.py
@IDE     ：PyCharm
@Author  ：杨逸轩
@Date    ：2023/12/02
"""

from PySide6.QtCore import QObject, QTimer

from utils.ip_checker import IPChecker
from utils.logger import Logger
from utils.threads import DNSUpdateThread, DNSInitThread, IPCheckThread, ThreadManager


class DNSUpdater(QObject):
    """DNS更新器，管理所有DNS平台的更新操作"""

    def __init__(self, config, main_window=None):
        """
        初始化DNS更新器
        Args:
            config: 配置对象
            main_window: 主窗口引用，用于显示消息
        """
        super().__init__()
        self.config = config
        self.main_window = main_window
        self.logger = Logger()
        self.platforms = {}  # 存储所有DNS平台实例
        self._timer = None  # 定时器
        self._running = False
        self._update_interval = config.get_update_interval()  # 更新间隔（秒）
        self.ip_checker = IPChecker()
        self._error_count = 0
        self._max_errors = 3
        self._thread_manager = ThreadManager.get_instance()
        self._retry_delays = [5, 15, 30]  # 重试延迟时间（秒）

    def start(self):
        """启动DNS更新服务"""
        self._running = True

        # 先加载平台
        self.reload_platforms()

        # 初始化定时器
        if not self._timer:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self.check_and_update)
            self._timer.start(self._update_interval * 1000)

    def set_update_interval(self, seconds):
        """
        设置更新间隔
        Args:
            seconds: 更新间隔（秒）
        """
        try:
            # 更新配置文件
            config_data = self.config.load_config()
            config_data['settings']['update_interval'] = seconds
            self.config.save_config(config_data)

            # 更新运行时间隔
            self._update_interval = max(30, seconds)  # 最小30秒

            # 重启定时器
            if self._timer and self._running:
                self._timer.stop()  # 先停止当前定时器
                self._timer.setInterval(self._update_interval * 1000)  # 设置新间隔
                self._timer.start()  # 重新启动定时器

        except Exception as e:
            self.logger.error(f"更新间隔设置失败: {str(e)}")

    def reload_platforms(self):
        """重新加载DNS平台"""
        # 清除现有平台
        self.platforms.clear()

        init_thread = DNSInitThread(self.config)
        init_thread.init_finished.connect(self._on_reload_finished)
        init_thread.error.connect(lambda e: self.logger.error(f"重新加载平台失败: {e}"))
        self._thread_manager.submit_thread(init_thread)

    def _on_reload_finished(self, new_platforms):
        """平台重新加载完成"""
        sender = self.sender()
        if sender in self._thread_manager._active_threads:
            self._thread_manager._active_threads.remove(sender)

        # 检查是否有变化
        old_platforms = set(self.platforms.keys())
        new_platform_keys = set(new_platforms.keys())

        # 更新平台列表
        self.platforms = new_platforms

        # 记录加载信息
        self.logger.info(f"DNS平台配置已加载，共 {len(new_platforms)} 个记录")

        # 如果是首次加载或有变化，立即进行一次检查
        if not old_platforms or old_platforms != new_platform_keys:
            QTimer.singleShot(100, self.check_and_update)

    def check_and_update(self):
        """检查并更新DNS记录"""
        if not self._running or not self.platforms:
            return

        # 检查IP
        ip_thread = IPCheckThread(self.ip_checker)
        ip_thread.ip_checked.connect(self._on_ip_checked)
        ip_thread.error.connect(lambda e: self.logger.error(f"IP检查失败: {e}"))
        self._thread_manager.submit_thread(ip_thread)

    def _on_ip_checked(self, ipv4, ipv6):
        """IP检查完成的回调"""
        sender = self.sender()
        if sender in self._thread_manager._active_threads:
            self._thread_manager._active_threads.remove(sender)

        if not (ipv4 or ipv6):
            self.logger.warning("未获取到任何IP地址")
            return

        for platform_key, platform in self.platforms.items():
            try:
                record_type = platform.config.get('record_type', 'A')
                current_ip = ipv4 if record_type == 'A' else ipv6

                if not current_ip:
                    self.logger.warning(f"{platform_key} - 未获取到{record_type}记录所需的IP地址")
                    continue

                # 先检查是否需要更新
                try:
                    current_records = platform.get_current_records()
                    current_record = current_records[0] if record_type == 'A' else current_records[1]

                    # 获取完整域名
                    full_domain = f"{platform.hostname}.{platform.domain}" if platform.hostname != '@' else platform.domain
                    platform_name = platform.__class__.__name__.replace('DNS', '').upper()
                    platform_key = f"[{platform_name}][{full_domain}]"

                    if current_record == current_ip:
                        self.logger.info(f"{platform_key} - 记录已是最新")
                        continue
                except Exception as e:
                    self.logger.error(f"{platform_key} - 检查记录失败: {str(e)}")
                    continue

                # 只有需要更新时才创建更新线程
                update_thread = DNSUpdateThread(platform, ipv4, ipv6)
                update_thread.error.connect(lambda e: self._on_update_error(e, platform, ipv4, ipv6))
                self._thread_manager.submit_thread(update_thread)

            except Exception as e:
                self.logger.error(f"{platform_key} - 处理出错: {str(e)}")

    def _retry_update(self, platform, ipv4, ipv6, retry_count=0):
        """重试更新"""
        if retry_count >= len(self._retry_delays):
            return

        delay = self._retry_delays[retry_count]
        self.logger.info(f"将在 {delay} 秒后重试更新...")
        QTimer.singleShot(delay * 1000, lambda: self._do_retry(platform, ipv4, ipv6, retry_count))

    def _do_retry(self, platform, ipv4, ipv6, retry_count):
        """执行重试"""
        if not self._running:
            return

        thread = DNSUpdateThread(platform, ipv4, ipv6)
        thread.error.connect(lambda e: self._on_update_error(e, platform, ipv4, ipv6, retry_count + 1))
        self._thread_manager.submit_thread(thread)

    def _on_update_error(self, error, platform, ipv4, ipv6):
        """更新错误处理"""
        platform_key = platform.get_platform_key()
        self.logger.error(f"{platform_key} - 更新失败: {error}")
        # 直接重试，因为已经确认需要更新
        self._retry_update(platform, ipv4, ipv6)

    def _on_update_finished(self, platform_key, success):
        """更新完成的回调"""
        sender = self.sender()
        if sender in self._thread_manager._active_threads:
            self._thread_manager._active_threads.remove(sender)

        # 不再显示任何消息，因为具体的成功/失败消息已经在 platform.update_records() 中处理了
        pass

    def stop(self):
        """停止DNS更新服务"""
        self._running = False
        if self._timer:
            self._timer.stop()

        # 停止所有线程
        self._thread_manager.stop_all()
