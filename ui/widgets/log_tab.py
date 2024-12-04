from PySide6.QtCore import QTimer
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit,
                               QPushButton, QHBoxLayout)

from utils.logger import Logger


class LogTab(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = Logger()

        # 添加初始测试日志
        self.logger.info("日志系统初始化成功")
        self.logger.debug("调试模式已启用")

        self.setup_ui()

        # 定时刷新日志
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_log)
        self.refresh_timer.start(500)  # 每500ms刷新一次

        # 设置日志颜色
        self.log_formats = {
            'INFO': QColor("#2ecc71"),  # 绿色
            'WARNING': QColor("#f1c40f"),  # 黄色
            'ERROR': QColor("#e74c3c"),  # 红色
            'DEBUG': QColor("#3498db"),  # 蓝色
            'timestamp': QColor("#95a5a6"),  # 灰色
        }

        # 立即刷新一次日志
        self.refresh_log()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setObjectName("logText")
        self.log_text.setReadOnly(True)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)  # 添加顶部边距

        self.clear_btn = QPushButton("清除日志")
        self.clear_btn.setObjectName("primaryButton")
        self.clear_btn.clicked.connect(self.clear_log)

        self.refresh_btn = QPushButton("刷新日志")
        self.refresh_btn.setObjectName("primaryButton")
        self.refresh_btn.clicked.connect(self.refresh_log)

        button_layout.addStretch()
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.clear_btn)

        layout.addWidget(self.log_text)
        layout.addLayout(button_layout)

    def append_colored_text(self, record):
        """添加带颜色的文本"""
        try:
            # 时间戳
            time_obj = record['time']
            time_str = time_obj.strftime('%Y-%m-%d %H:%M:%S')
            self.append_text(f"{time_str} | ", self.log_formats['timestamp'])

            # 日志级别
            level = record['level'].name
            level_color = self.log_formats.get(level, QColor("#2f3542"))
            self.append_text(f"{level:8} | ", level_color)

            # 消息内容
            self.append_text(f"{record['message']}\n", level_color)
        except Exception as e:
            self.append_text(f"Error formatting log: {str(e)}\n", self.log_formats['ERROR'])

    def append_text(self, text, color):
        cursor = self.log_text.textCursor()
        format = QTextCharFormat()
        format.setForeground(color)
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text, format)
        self.log_text.setTextCursor(cursor)

    def refresh_log(self):
        """刷新日志内容"""
        try:
            # 获取当前日志数量
            current_count = self.log_text.document().lineCount()

            # 获取新日志
            buffer = self.logger.get_buffer()

            # 如果有新日志，添加到显示区域
            if len(buffer) > current_count - 1:  # -1 因为空文档的行数是1
                for record in buffer[current_count - 1:]:
                    self.append_colored_text(record)

                # 滚动到底部
                scrollbar = self.log_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            self.append_text(f"Error refreshing log: {str(e)}\n", self.log_formats['ERROR'])

    def clear_log(self):
        """清除日志"""
        self.log_text.clear()
        self.logger.clear_buffer()
        self.logger.info("日志已清除")
