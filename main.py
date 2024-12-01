import sys

from PySide6.QtWidgets import QApplication

from config import Config
from ui.main_window import MainWindow
from utils.dns_updater import DNSUpdater
from utils.ip_checker import IPChecker

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 创建配置对象
    config = Config()

    # 创建IP检查器
    ip_checker = IPChecker()

    # 先创建主窗口
    window = MainWindow(config, ip_checker, None)

    # 再创建DNS更新器并设置主窗口
    dns_updater = DNSUpdater(config, window)
    window.dns_updater = dns_updater
    window.set_dns_updater(dns_updater)

    window.show()

    sys.exit(app.exec())
