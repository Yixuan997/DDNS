from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget

from ui.styles.main_style import MainStyle


class MessageDialog(QDialog):
    def __init__(self, parent=None, title="提示", message="", type="info"):
        """
        type: 'info', 'warning', 'error', 'confirm'
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(400)
        self.setStyleSheet(MainStyle.get_style())
        self.old_pos = None
        self.type = type
        self.setup_ui(title, message)

    def setup_ui(self, title, message):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 主容器
        main_widget = QWidget()
        main_widget.setObjectName("inner_widget")
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 消息区域
        message_label = QLabel(message)
        message_label.setObjectName("messageLabel")
        message_label.setWordWrap(True)
        main_layout.addWidget(message_label)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)

        if self.type == 'confirm':
            # 取消按钮
            cancel_btn = QPushButton("取消")
            cancel_btn.setObjectName("primaryButton")
            cancel_btn.setProperty("delete", "true")
            cancel_btn.clicked.connect(self.reject)

            # 确定按钮
            ok_btn = QPushButton("确定")
            ok_btn.setObjectName("primaryButton")
            ok_btn.clicked.connect(self.accept)

            button_layout.addStretch()
            button_layout.addWidget(cancel_btn)
            button_layout.addWidget(ok_btn)
        else:
            # 确定按钮
            ok_btn = QPushButton("确定")
            ok_btn.setObjectName("primaryButton")
            if self.type == 'error':
                ok_btn.setProperty("delete", "true")
            ok_btn.clicked.connect(self.accept)

            button_layout.addStretch()
            button_layout.addWidget(ok_btn)

        main_layout.addLayout(button_layout)
        layout.addWidget(main_widget)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.old_pos:
            return
        delta = QPoint(event.globalPos() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None
