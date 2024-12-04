from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QApplication, QTabWidget, QSystemTrayIcon, QMenu)

from ui.dialogs.about_dialog import AboutDialog
from ui.dialogs.message_dialog import MessageDialog
from ui.styles.main_style import MainStyle
from ui.widgets.dns_tab import DNSTab
from ui.widgets.log_tab import LogTab
from ui.widgets.settings_tab import SettingsTab
from ui.widgets.status_tab import StatusTab
from ui.widgets.title_bar import TitleBar
from ui.widgets.toast import ToastWidget
from utils.logger import Logger
from utils.resource_manager import ResourceManager


class MainWindow(QMainWindow):
    def __init__(self, config, ip_checker, dns_updater):
        super().__init__()
        self.config = config
        self.ip_checker = ip_checker
        self.dns_updater = dns_updater
        self.logger = Logger()

        # 设置窗口属性
        self.setWindowIcon(ResourceManager.get_icon("icon.svg"))
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("DDNS Client")
        self.setMinimumSize(800, 500)

        self.setup_ui()
        self.apply_styles()
        self._drag_pos = None
        self.setup_tray_icon()

    def setup_ui(self):
        # 创建主窗口部件
        self.central_widget = QWidget()
        self.central_widget.setObjectName("central_widget")
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(0)

        # 创建内部容器
        self.inner_widget = QWidget()
        self.inner_widget.setObjectName("inner_widget")
        inner_layout = QVBoxLayout(self.inner_widget)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(0)

        # 创建标题栏
        self.title_bar = TitleBar(self)
        inner_layout.addWidget(self.title_bar)

        # 创建内容区域
        content_widget = QWidget()
        content_widget.setObjectName("content_widget")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 5, 15, 15)
        content_layout.setSpacing(10)

        # 创建选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTab")

        # 添加各个页面
        self.status_tab = StatusTab(self.ip_checker, self, self.config, self.dns_updater)
        self.dns_tab = DNSTab(self.config, self)
        self.settings_tab = SettingsTab(self.config, self)
        self.log_tab = LogTab(self.config)
        self.about_tab = AboutDialog(self)

        self.tab_widget.addTab(self.status_tab, "状态")
        self.tab_widget.addTab(self.dns_tab, "DNS设置")
        self.tab_widget.addTab(self.settings_tab, "设置")
        self.tab_widget.addTab(self.log_tab, "日志")
        self.tab_widget.addTab(self.about_tab, "关于")

        content_layout.addWidget(self.tab_widget)
        inner_layout.addWidget(content_widget)
        self.main_layout.addWidget(self.inner_widget)

        # 创建消息提示组件
        self.toast = ToastWidget(self)

    def apply_styles(self):
        self.setStyleSheet(MainStyle.get_style())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            new_pos = event.globalPosition().toPoint()
            self.move(self.pos() + new_pos - self._drag_pos)
            self._drag_pos = new_pos

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def show_message(self, message, status="success"):
        """显示消息提示（Toast形式）"""
        self.toast.show_message(message, status)

    def show_dialog(self, message, type="info"):
        """显示对话框"""
        dialog = MessageDialog(self, message=message, type=type)
        return dialog.exec_()

    def setup_tray_icon(self):
        """设置系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(ResourceManager.get_icon("icon.svg"))
        self.tray_icon.setToolTip("DDNS Client")

        # 创建托盘菜单
        tray_menu = QMenu()

        # 显示主窗口动作
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        # 分隔线
        tray_menu.addSeparator()

        # 退出动作
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # 托盘图标击显示主窗口
        self.tray_icon.activated.connect(self._on_tray_activated)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def closeEvent(self, event):
        # 使用对话框请求确认
        if self.show_dialog("确定要退出程序吗？\n点击取消将最小化到系统托盘。", "confirm"):
            event.accept()
            self.tray_icon.hide()
            QApplication.quit()
        else:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "DDNS Client",
                "程序已最小化到系统托盘",
                QSystemTrayIcon.Information,
                2000
            )

    def quit_application(self):
        """退出应用程序"""
        self.tray_icon.hide()  # 隐藏托盘图标
        QApplication.quit()  # 退出程序

    def set_dns_updater(self, dns_updater):
        """设置DNS更新器"""
        self.dns_updater = dns_updater
        if hasattr(self, 'status_tab'):
            self.status_tab.dns_updater = dns_updater
