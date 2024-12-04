"""
@Project ：DDNS
@File    ：dns_updater.py
@IDE     ：PyCharm
@Author  ：杨逸轩
@Date    ：2023/12/02
"""

from PySide6.QtCore import QObject, QTimer
from utils.threads import DNSUpdateThread, DNSInitThread, IPCheckThread

from utils.logger import Logger
from utils.memory_tracker import MemoryTracker
from utils.ip_checker import IPChecker


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
        self._threads = []  # 存储所有活动线程

    def start(self):
        """启动DNS更新服务"""
        # 初始化定时器
        if not self._timer:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self.check_and_update)

        self._running = True
        self._timer.start(self._update_interval * 1000)

        # 立即进行一次检查
        QTimer.singleShot(100, self.check_and_update)

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
        init_thread = DNSInitThread(self.config)
        init_thread.init_finished.connect(self._on_reload_finished)
        init_thread.error.connect(lambda e: self.logger.error(f"重新加载平台失败: {e}"))
        self._threads.append(init_thread)
        init_thread.start()

    def _on_reload_finished(self, new_platforms):
        """平台重新加载完成"""
        sender = self.sender()
        if sender in self._threads:
            self._threads.remove(sender)

        # 检查是否有变化
        old_platforms = set(self.platforms.keys())
        new_platform_keys = set(new_platforms.keys())
        has_changes = old_platforms != new_platform_keys

        # 更新平台列表
        self.platforms = new_platforms

        # 如果有变化，立即进行一次检查
        if has_changes:
            QTimer.singleShot(100, self.check_and_update)

    def check_and_update(self):
        """检查并更新DNS记录"""
        if not self._running:
            return

        # 先重新加载平台配置
        self.reload_platforms()

        # 然后检查IP
        ip_thread = IPCheckThread(self.ip_checker)
        ip_thread.ip_checked.connect(self._on_ip_checked)
        ip_thread.error.connect(lambda e: self.logger.error(f"IP检查失败: {e}"))
        self._threads.append(ip_thread)
        ip_thread.start()

    def _on_ip_checked(self, ipv4, ipv6):
        """IP检查完成的回调"""
        sender = self.sender()
        if sender in self._threads:
            self._threads.remove(sender)

        if not (ipv4 or ipv6):
            return

        for platform_key, platform in self.platforms.items():
            try:
                record_type = platform.config.get('record_type', 'A')
                current_ip = ipv4 if record_type == 'A' else ipv6

                if current_ip:
                    update_thread = DNSUpdateThread(platform, ipv4, ipv6)
                    update_thread.update_finished.connect(self._on_update_finished)
                    update_thread.error.connect(lambda e: self.logger.error(f"{platform_key} - 更新失败: {e}"))
                    self._threads.append(update_thread)
                    update_thread.start()

            except Exception as e:
                self.logger.error(f"{platform_key} - 处理出错: {str(e)}")

    def _on_update_finished(self, platform_key, success):
        """更新完成的回调"""
        sender = self.sender()
        if sender in self._threads:
            self._threads.remove(sender)

        if success:
            self.logger.info(f"{platform_key} - 更新成功")
            if self.main_window:
                self.main_window.show_message(f"{platform_key} 更新成功", "success")
        else:
            self.logger.error(f"{platform_key} - 更新失败")
            if self.main_window:
                self.main_window.show_message(f"{platform_key} 更新失败", "error")

    def stop(self):
        """停止DNS更新服务"""
        self._running = False
        if self._timer:
            self._timer.stop()

        # 停止所有线程
        for thread in self._threads:
            thread.quit()
            thread.wait()
        self._threads.clear()
