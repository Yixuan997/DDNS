from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout

from utils.resource_manager import ResourceManager


class ToastWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setParent(parent)
        self.setWindowFlags(Qt.Widget)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setup_ui()
        self.setup_animation()
        self.apply_styles()
        self.hide()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # 容器widget
        container = QWidget()
        container.setObjectName("container")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(12, 6, 12, 6)
        container_layout.setSpacing(8)

        # 图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        self.success_icon = ResourceManager.get_icon("success.svg").pixmap(16, 16)
        self.error_icon = ResourceManager.get_icon("error.svg").pixmap(16, 16)
        container_layout.addWidget(self.icon_label)

        # 消息文本
        self.label = QLabel()
        self.label.setMinimumWidth(200)
        container_layout.addWidget(self.label)

        layout.addWidget(container)

    def setup_animation(self):
        # 动画
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(500)
        self.animation.finished.connect(self._on_animation_finished)

        # 显示定时器
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_message)

    def apply_styles(self):
        self.setStyleSheet("""
            ToastWidget {
                background: transparent;
            }

            #container {
                background-color: rgba(0, 0, 0, 0.75);
                border-radius: 4px;
            }

            ToastWidget[status="success"] #container {
                background-color: rgba(46, 204, 113, 0.85);
            }

            ToastWidget[status="error"] #container {
                background-color: rgba(231, 76, 60, 0.85);
            }

            QLabel {
                color: white;
                font-size: 13px;
            }
        """)

    def show_message(self, message, status="success"):
        # 停止之前的动画和定时器
        self.animation.stop()
        self.timer.stop()
        self.hide()

        # 设置消息内容
        if len(message) > 50:
            message = message[:47] + "..."
        self.label.setText(message)
        self.icon_label.setPixmap(self.success_icon if status == "success" else self.error_icon)

        self.setProperty("status", status)
        self.style().unpolish(self)
        self.style().polish(self)

        self.adjustSize()

        # 显示消息
        parent = self.parent()
        if parent:
            target_x = (parent.width() - self.width()) // 2
            target_y = 45  # 固定显示位置

            # 设置动画
            self.animation.setStartValue(QPoint(target_x, -100))
            self.animation.setEndValue(QPoint(target_x, target_y))

            # 显示并开始动画
            self.show()
            self.raise_()
            self.animation.start()

            # 3.5秒后隐藏
            self.timer.start(3500)

    def hide_message(self):
        """开始隐藏动画"""
        if not self.isVisible():
            return

        current_pos = self.pos()
        self.animation.setStartValue(current_pos)
        self.animation.setEndValue(QPoint(current_pos.x(), -100))
        self.animation.start()

    def _on_animation_finished(self):
        """动画完成的统一处理"""
        if self.pos().y() < 0:  # 如果位置在屏幕外，说明是隐藏动画完成
            self.hide()
