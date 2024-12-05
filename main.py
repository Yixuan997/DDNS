"""
@Project ：DDNS
@File    ：main.py
@IDE     ：PyCharm
@Author  ：杨逸轩
@Date    ：2023/12/02
"""

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from config import Config
from ui.main_window import MainWindow
from utils.dns_updater import DNSUpdater
from utils.ip_checker import IPChecker
from utils.logger import Logger
from utils.memory_tracker import MemoryTracker

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dns_updater = None
    memory_timer = None

    try:
        logger = Logger()
        config = Config()
        ip_checker = IPChecker()

        # 创建主窗口并立即显示
        window = MainWindow(config, ip_checker, None)
        window.setWindowOpacity(1.0)
        window.show()
        app.processEvents()


        # 延迟初始化DNS更新器和其他功能
        def delayed_init():
            global dns_updater, memory_timer
            # 创建DNS更新器但不立即启动
            dns_updater = DNSUpdater(config, window)
            window.dns_updater = dns_updater
            window.set_dns_updater(dns_updater)

            # 设置内存监控
            memory_timer = QTimer()
            memory_timer.timeout.connect(MemoryTracker.log_memory_usage)
            memory_timer.start(300000)

            # 延迟1秒后启动DNS更新器
            QTimer.singleShot(1000, dns_updater.start)


        # 延迟初始化
        QTimer.singleShot(500, delayed_init)

        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"程序发生异常: {str(e)}")
    finally:
        try:
            if dns_updater:
                dns_updater.stop()
            if 'window' in locals():
                window.close()
            if memory_timer:
                memory_timer.stop()
        except Exception as cleanup_error:
            logger.error(f"清理资源时发生错误: {str(cleanup_error)}")

        app.quit()
