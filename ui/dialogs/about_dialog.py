from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar, QHBoxLayout

from utils.resource_manager import ResourceManager
from utils.updater import Updater


class AboutDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.updater = Updater()
        self.setup_ui()

    def setup_ui(self):
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 40, 30, 40)
        layout.setSpacing(20)

        # Logo
        logo_label = QLabel()
        pixmap = ResourceManager.get_icon("icon.svg").pixmap(80, 80)
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # 标题
        title_label = QLabel("DDNS Client")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 版本和更新
        version_layout = QHBoxLayout()
        version_layout.setSpacing(10)

        version_label = QLabel(f"Version {self.updater.CURRENT_VERSION}")
        version_font = QFont()
        version_font.setPointSize(12)
        version_label.setFont(version_font)
        version_label.setAlignment(Qt.AlignCenter)
        version_layout.addWidget(version_label)

        # 检查更新按钮
        self.update_btn = QPushButton("检查更新")
        self.update_btn.setObjectName("primaryButton")
        self.update_btn.setFixedSize(100, 32)
        self.update_btn.clicked.connect(self.check_update)
        version_layout.addWidget(self.update_btn)

        version_layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(version_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setVisible(False)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)
        layout.addLayout(progress_layout)

        # 分隔线
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #e1e5ee;")
        layout.addWidget(line)

        # 描述
        desc_label = QLabel(
            "DDNS Client 是一个跨平台的动态域名解析客户端，\n"
            "支持多个DNS平台，可以自动更新域名解析记录。"
        )
        desc_font = QFont()
        desc_font.setPointSize(11)
        desc_label.setFont(desc_font)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #666;")
        layout.addWidget(desc_label)

        # 作者
        author_label = QLabel("作者: 杨逸轩")
        author_label.setAlignment(Qt.AlignCenter)
        author_label.setStyleSheet("color: #666;")
        layout.addWidget(author_label)

        # GitHub链接
        github_label = QLabel(
            '<a href="https://github.com/Yixuan997/DDNS" style="color: #5352ed; text-decoration: none;">GitHub</a>')
        github_label.setOpenExternalLinks(True)
        github_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(github_label)

        # 添加弹性空间
        layout.addStretch()

    def check_update(self):
        """检查更新"""
        if not self.parent:  # 确保有父窗口
            return

        self.update_btn.setEnabled(False)
        self.update_btn.setText("检查中...")

        try:
            has_update, update_info = self.updater.check_update()

            if has_update and update_info:  # 确保 update_info 不为 None
                # 显示更新确认对话框
                if self.parent.show_dialog(
                        f"发现新版本: v{update_info['version']}\n\n"
                        f"{update_info['description']}\n\n"
                        "是否立即更新？",
                        "confirm"
                ):
                    self.start_download(update_info['download_url'])
            else:
                self.parent.show_message("当前已是最新版本", "success")

        except Exception as e:
            if self.parent:
                self.parent.show_message("检查更新失败", "error")

        finally:
            if not self.isHidden():  # 确保窗口还在
                self.update_btn.setEnabled(True)
                self.update_btn.setText("检查更新")

    def start_download(self, url):
        """开始下载"""
        if not self.parent:
            return

        try:
            self.progress_bar.setVisible(True)
            self.update_btn.setText("下载中...")
            self.update_btn.setEnabled(False)

            def progress_callback(value):
                if not self.isHidden():  # 确保窗口还在
                    self.progress_bar.setValue(value)
                    if value >= 100:
                        self.download_complete()

            # 在新线程中下载
            temp_file = self.updater.download_update(url, progress_callback)
            if temp_file:
                self.parent.show_dialog("更新下载完成，重启程序后生效", "info")
            else:
                self.parent.show_message("下载更新失败", "error")

        except Exception as e:
            if self.parent:
                self.parent.show_message("下载更新失败", "error")

        finally:
            if not self.isHidden():  # 确保窗口还在
                self.download_complete()

    def download_complete(self):
        """下载完成"""
        if not self.isHidden():  # 确保窗口还在
            self.progress_bar.setVisible(False)
            self.update_btn.setEnabled(True)
            self.update_btn.setText("检查更新")
