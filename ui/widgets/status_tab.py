"""
@Project ：DDNS
@File    ：status_tab.py
@IDE     ：PyCharm
@Author  ：杨逸轩
@Date    ：2023/12/02
"""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QGroupBox)

from utils.logger import Logger
from utils.threads import ThreadManager, IPCheckThread  # 从 threads 模块导入


class StatusTab(QWidget):
    """状态标签页，显示IP地址和DNS更新状态"""

    def __init__(self, ip_checker, main_window, config, dns_updater):
        """
        初始化状态标签页
        Args:
            ip_checker: IP检查器实例
            main_window: 主窗口实例
            config: 配置对象
            dns_updater: DNS更新器实例
        """
        super().__init__()
        self.ip_checker = ip_checker
        self.main_window = main_window
        self.config = config
        self.dns_updater = dns_updater
        self.logger = Logger()
        self.setup_ui()

        # 设置定时刷新
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(lambda: self.refresh_ip(True))
        self.update_refresh_interval()

        # 立即进行一次IP检查
        self.initial_check()

    def set_dns_updater(self, dns_updater):
        """
        设置DNS更新器
        Args:
            dns_updater: DNS更新器实例
        """
        self.dns_updater = dns_updater
        # 不立即启动定时器，等待DNS更新器的第一次检查完成后再启动
        # self.refresh_timer.start()

    def initial_check(self):
        """初始IP检查，只更新界面显示，不进行DNS更新"""
        try:
            ipv4, ipv6 = self.ip_checker.get_current_ips()
            self.on_ip_checked(ipv4, ipv6, False, False)
        except Exception as e:
            self.logger.error("初始IP检查失败")

    def refresh_ip(self, show_message=False):
        """刷新IP地址"""
        ip_thread = IPCheckThread(self.ip_checker)
        ip_thread.success.connect(lambda ip_data: self.on_ip_checked(*ip_data, show_message, show_message))
        ip_thread.error.connect(lambda e: self.logger.error(f"IP检查失败: {e}"))
        ThreadManager.instance().submit_thread(ip_thread)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # IP状态卡片
        ip_group = QGroupBox("IP 状态")
        ip_group.setObjectName("statusCard")
        ip_layout = QVBoxLayout(ip_group)

        # IPv4状态
        ipv4_widget = QWidget()
        ipv4_layout = QHBoxLayout(ipv4_widget)
        ipv4_layout.setContentsMargins(0, 0, 0, 0)

        ipv4_title = QLabel("IPv4:")
        ipv4_title.setObjectName("ipLabel")
        self.ipv4_label = QLabel("获取中...")
        self.ipv4_label.setObjectName("ipValue")

        ipv4_layout.addWidget(ipv4_title)
        ipv4_layout.addWidget(self.ipv4_label)
        ipv4_layout.addStretch()

        # IPv6状态
        ipv6_widget = QWidget()
        ipv6_layout = QHBoxLayout(ipv6_widget)
        ipv6_layout.setContentsMargins(0, 0, 0, 0)

        ipv6_title = QLabel("IPv6:")
        ipv6_title.setObjectName("ipLabel")
        self.ipv6_label = QLabel("获取中...")
        self.ipv6_label.setObjectName("ipValue")

        ipv6_layout.addWidget(ipv6_title)
        ipv6_layout.addWidget(self.ipv6_label)
        ipv6_layout.addStretch()

        ip_layout.addWidget(ipv4_widget)
        ip_layout.addWidget(ipv6_widget)

        # 刷新按钮
        refresh_btn = QPushButton("立即刷新")
        refresh_btn.setObjectName("primaryButton")
        refresh_btn.clicked.connect(self.on_refresh_clicked)

        # 状态日志
        status_group = QGroupBox("运行状态")
        status_group.setObjectName("statusCard")
        status_layout = QVBoxLayout(status_group)

        # 状态指示器
        status_widget = QWidget()
        status_widget_layout = QHBoxLayout(status_widget)
        status_widget_layout.setContentsMargins(0, 0, 0, 0)

        self.status_indicator = QLabel("●")
        self.status_indicator.setObjectName("statusIndicator")
        status_widget_layout.addWidget(self.status_indicator)

        self.status_label = QLabel("运行正常")
        self.status_label.setObjectName("statusLabel")
        status_widget_layout.addWidget(self.status_label)
        status_widget_layout.addStretch()

        # 上次更新时间
        self.last_update_label = QLabel("上次更新: 未更新")
        self.last_update_label.setObjectName("lastUpdateLabel")

        status_layout.addWidget(status_widget)
        status_layout.addWidget(self.last_update_label)

        layout.addWidget(ip_group)
        layout.addWidget(refresh_btn)
        layout.addWidget(status_group)
        layout.addStretch()

    def update_refresh_interval(self):
        """更新刷新间隔"""
        if self.config:
            interval = self.config.get_update_interval()
            self.refresh_timer.setInterval(interval * 1000)
            self.refresh_timer.start()

    def update_status(self, status="normal", message=None):
        """更新状态显示
        status: normal, warning, error
        """
        status_map = {
            "normal": ("运行正常", "#2ecc71"),
            "warning": ("注意", "#f1c40f"),
            "error": ("异常", "#e74c3c")
        }

        status_text, color = status_map.get(status, status_map["normal"])
        if message:
            status_text = message

        self.status_indicator.setStyleSheet(f"#statusIndicator {{ color: {color}; }}")
        self.status_label.setText(status_text)

    def update_last_check_time(self):
        """更新上次检查时间"""
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_update_label.setText(f"上次更新: {now}")

    def on_ip_checked(self, ipv4, ipv6, show_message=False, force_message=False):
        """IP检查完成的回调
        Args:
            ipv4: IPv4地址
            ipv6: IPv6地址
            show_message: 是否显示消息
            force_message: 是否强制显示消息
        """
        old_ipv4 = self.ipv4_label.text()
        old_ipv6 = self.ipv6_label.text()

        # 更新IP显示
        if ipv4:
            self.ipv4_label.setText(ipv4)
        else:
            self.ipv4_label.setText("未获取到")

        if ipv6:
            self.ipv6_label.setText(ipv6)
        else:
            self.ipv6_label.setText("未获取到")

        # 更新状态显示
        if ipv4 and ipv6:
            self.update_status("normal", "运行正常")
        elif ipv4:
            self.update_status("warning", "无法获取IPv6地址")
        elif ipv6:
            self.update_status("warning", "无法获取IPv4地址")
        else:
            self.update_status("error", "无法获取IP地址")

        # 更新上次检查时间
        self.update_last_check_time()

        # 检查IP是否变化
        has_changes = old_ipv4 != self.ipv4_label.text() or old_ipv6 != self.ipv6_label.text()

        # 当IP变化或强制显示消息时显示提示
        if show_message and (has_changes or force_message):
            if self.main_window:
                if not ipv4 and not ipv6:
                    self.main_window.show_message("无法获取IP地址", "error")
                elif has_changes:
                    self.main_window.show_message("IP地址已更新", "success")
                else:
                    self.main_window.show_message("IP地址未发生变化", "success")

        # 在第一次IP检查完成后启动定时器
        if not self.refresh_timer.isActive():
            self.refresh_timer.start()

    def on_refresh_clicked(self):
        """刷新按钮点击处理"""
        self.refresh_ip(True)  # 手动刷新时显示消息
