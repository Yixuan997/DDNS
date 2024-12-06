from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar, QHBoxLayout

from utils.resource_manager import ResourceManager
from utils.updater import Updater
from utils.logger import Logger


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
        self.progress_bar.setFixedWidth(300)  # 增加宽度
        self.progress_bar.setFixedHeight(4)  # 减小高度，使其更现代
        self.progress_bar.setTextVisible(False)  # 隐藏文字
        self.progress_bar.setVisible(False)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        # 设置进度条样式
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #f0f0f0;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #5352ed;
                border-radius: 2px;
            }
        """)
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

        # 禁用按钮并更改状态
        self.update_btn.setEnabled(False)
        self.update_btn.setText("检查中...")
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #e1e5ee;
                color: #666666;
            }
        """)

        def update_callback(result):
            """更新检查的回调函数"""
            has_update, update_info = result
            try:
                if has_update and update_info:
                    # Logger().debug(f"检测到新版本: {update_info.get('version')}")
                    # 显示更新确认对话框
                    if self.parent.show_dialog(
                            f"发现新版本: v{update_info['version']}\n\n"
                            f"{update_info['description']}\n\n"
                            "是否立即更新？",
                            "confirm"
                    ):
                        self.start_download(update_info['download_url'])
                    else:
                        self._reset_button_state()
                elif update_info and 'error' in update_info:
                    # 显示错误信息
                    error_msg = f"检查更新失败: {update_info['error']}"
                    self.parent.show_message(error_msg, "error")
                    self._reset_button_state()
                else:
                    self.parent.show_message("当前已是最新版本", "success")
                    self._reset_button_state()
            except Exception as e:
                error_msg = f"处理更新信息失败: {str(e)}"
                self.parent.show_message(error_msg, "error")
                self._reset_button_state()

        try:
            # 使用回调函数方式调用
            self.updater.check_update(update_callback)
        except Exception as e:
            error_msg = f"启动更新检查失败: {str(e)}"
            if self.parent:
                self.parent.show_message(error_msg, "error")
            self._reset_button_state()

    def start_download(self, url):
        """开始下载"""
        if not self.parent:
            return

        try:
            # 获取镜像地址列表
            from utils.updater import UpdateMirrors
            mirrors = UpdateMirrors()
            mirror_urls = mirrors.get_download_urls(url)
            if not mirror_urls:
                self.parent.show_message("未能生成有效的镜像地址", "error")
                return

            # 使用第一个镜像地址
            download_url = mirror_urls[0]
            # 显示进度条并设置按钮状态
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.update_btn.setText("准备下载...")
            self.update_btn.setEnabled(False)
            self.update_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e1e5ee;
                    color: #666666;
                }
            """)

            def progress_callback(value):
                if not self.isHidden():  # 确保窗口还在
                    self.progress_bar.setValue(value)
                    if value < 100:
                        self.update_btn.setText(f"下载中 {value}%")
                    else:
                        self.update_btn.setText("完成")

            def download_success(file_path):
                if not self.isHidden():
                    self.parent.show_message("更新下载完成，重启程序后生效", "success")
                    self.download_complete()

            def download_error(error):
                    self.parent.show_message(f"下载失败: {error}", "error")
                    self.download_complete()

            # 创建下载线程
            from utils.threads import UpdateDownloadThread
            download_thread = UpdateDownloadThread(download_url)  # 使用镜像地址
            download_thread.progress.connect(progress_callback)
            download_thread.success.connect(download_success)
            download_thread.error.connect(download_error)

            from utils.threads import ThreadManager
            ThreadManager.instance().submit_thread(download_thread)

        except Exception as e:
            error_msg = f"启动更新下载失败: {str(e)}"
            Logger().error(error_msg)
            if self.parent:
                self.parent.show_message(error_msg, "error")
            self.download_complete()

    def download_complete(self):
        """下载完成"""
        if not self.isHidden():  # 确保窗口还在
            self.progress_bar.setVisible(False)
            self.progress_bar.setValue(0)
            self._reset_button_state()
            Logger().info("更新下载流程结束")

    def _reset_button_state(self):
        """重置按钮状态"""
        if not self.isHidden():  # 确保窗口还在
            self.update_btn.setEnabled(True)
            self.update_btn.setText("检查更新")
            self.update_btn.setStyleSheet("")  # 恢复默认样式
