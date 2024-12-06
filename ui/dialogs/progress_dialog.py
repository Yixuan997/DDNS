from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QWidget, QPushButton


class CustomProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setTextVisible(False)
        self.setFixedHeight(4)
        self.setStyleSheet("""
            QProgressBar {
                background-color: #F0F0F0;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #4A90E2;
                border-radius: 2px;
            }
        """)


class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 100)

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 内容容器
        container = QWidget(self)
        container.setObjectName("progressContainer")
        container.setStyleSheet("""
            #progressContainer {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
            }
        """)

        # 容器布局
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 15, 20, 15)
        container_layout.setSpacing(10)

        # 标题
        self.title_label = QLabel("正在下载更新...")
        self.title_label.setStyleSheet("font-size: 14px; color: #333333;")

        # 进度条
        self.progress_bar = CustomProgressBar()

        # 进度文本
        self.progress_label = QLabel("0%")
        self.progress_label.setStyleSheet("font-size: 12px; color: #666666;")
        self.progress_label.setAlignment(Qt.AlignRight)

        # 添加取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("cancelButton")
        self.cancel_btn.setStyleSheet("""
            #cancelButton {
                background: transparent;
                border: none;
                color: #666666;
                padding: 5px;
            }
            #cancelButton:hover {
                color: #333333;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)

        # 添加组件
        container_layout.addWidget(self.title_label)
        container_layout.addWidget(self.progress_bar)
        container_layout.addWidget(self.progress_label)
        container_layout.addWidget(self.cancel_btn, alignment=Qt.AlignRight)

        # 添加容器到主布局
        layout.addWidget(container)

        # 设置窗口样式
        self.setStyleSheet("""
            ProgressDialog {
                background: transparent;
            }
        """)

    def set_progress(self, value):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(f"{value}%")

    def paintEvent(self, event):
        """绘制阴影"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 设置阴影颜色和透明度
        shadow_color = QColor(0, 0, 0, 30)
        painter.setPen(Qt.NoPen)
        painter.setBrush(shadow_color)

        # 绘制圆角矩形阴影
        painter.drawRoundedRect(10, 10, self.width() - 20, self.height() - 20, 8, 8)

    def reject(self):
        """取消下载"""
        if hasattr(self.parent(), 'download_thread'):
            self.parent().download_thread.stop()
        super().reject()
