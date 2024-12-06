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
from utils.threads import ThreadManager, DNSInitThread, IPCheckThread, DNSUpdateThread


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
        self._thread_manager = ThreadManager.instance()

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
        self.platforms.clear()

        init_thread = DNSInitThread(self.config)
        init_thread.success.connect(self._on_reload_finished)
        init_thread.error.connect(lambda e: self.logger.error(f"重新加载平台失败: {e}"))
        self._thread_manager.submit_thread(init_thread)

    def _on_reload_finished(self, new_platforms):
        """平台重新加载完成"""
        self.platforms = new_platforms
        self.logger.info(f"DNS平台配置已加载，共 {len(new_platforms)} 个记录")
        QTimer.singleShot(100, self.check_and_update)

    def check_and_update(self):
        """检查并更新DNS记录"""
        if not self._running or not self.platforms:
            return

        ip_thread = IPCheckThread(self.ip_checker)
        ip_thread.success.connect(self._on_ip_checked)
        ip_thread.error.connect(lambda e: self.logger.error(f"IP检查失败: {e}"))
        self._thread_manager.submit_thread(ip_thread)

    def _on_ip_checked(self, ip_data):
        """IP检查完成的回调"""
        ipv4, ipv6 = ip_data
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

                update_thread = DNSUpdateThread(platform, ipv4, ipv6)
                update_thread.success.connect(lambda result, p=platform: self._on_update_success(result, p))
                update_thread.error.connect(lambda e, p=platform: self._on_update_error(e, p))
                self._thread_manager.submit_thread(update_thread)

            except Exception as e:
                self.logger.error(f"{platform_key} - 处理出错: {str(e)}")

    def _on_update_success(self, updated, platform):
        """更新成功的处理"""
        if updated:
            self.logger.info(f"{platform.get_platform_key()} - 更新成功")
        # 不需要处理 False 的情况，因为日志已经在线程中输出

    def _on_update_error(self, error, platform):
        """更新错误的处理"""
        self.logger.error(f"{platform.get_platform_key()} - {error}")

    def stop(self):
        """停止DNS更新服务"""
        self._running = False
        if self._timer:
            self._timer.stop()

        # 停止所有线程
        self._thread_manager.stop_all()
