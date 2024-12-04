from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

from utils.resource_manager import ResourceManager


class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # 窗口图标
        icon_label = QLabel()
        icon_label.setPixmap(ResourceManager.get_icon("icon.svg").pixmap(16, 16))
        icon_label.setFixedSize(16, 16)
        layout.addWidget(icon_label)

        # 窗口标题
        title_label = QLabel("DDNS Client")
        title_label.setObjectName("windowTitle")
        title_label.setContentsMargins(5, 0, 0, 0)
        layout.addWidget(title_label)

        layout.addStretch()

        # 右侧按钮容器
        self.right_buttons = QHBoxLayout()
        self.right_buttons.setSpacing(0)
        layout.addLayout(self.right_buttons)

        # 最小化按钮
        min_btn = QPushButton("⚊")
        min_btn.setObjectName("minButton")
        min_btn.clicked.connect(self.parent.showMinimized)

        # 最大化/还原按钮
        self.max_btn = QPushButton("☐")
        self.max_btn.setObjectName("maxButton")
        self.max_btn.clicked.connect(self.toggle_maximize)

        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.clicked.connect(self.parent.close)

        self.right_buttons.addWidget(min_btn)
        self.right_buttons.addWidget(self.max_btn)
        self.right_buttons.addWidget(close_btn)

    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.max_btn.setText("☐")
        else:
            self.parent.showMaximized()
            self.max_btn.setText("❐")

    def addWidget(self, widget):
        """添加自定义按钮到标题栏"""
        # 在最小化按钮之前插入新按钮
        self.right_buttons.insertWidget(0, widget)
