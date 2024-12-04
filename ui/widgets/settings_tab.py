from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout,
                               QPushButton, QLineEdit, QGroupBox, QCheckBox,
                               QHBoxLayout, QLabel)


class SettingsTab(QWidget):
    def __init__(self, config, main_window):
        super().__init__()
        self.config = config
        self.main_window = main_window
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 常规设置卡片
        settings_group = QGroupBox("常规设置")
        settings_group.setObjectName("configCard")
        settings_layout = QFormLayout(settings_group)
        settings_layout.setSpacing(15)

        # 更新间隔设置
        interval_widget = QWidget()
        interval_layout = QHBoxLayout(interval_widget)
        interval_layout.setContentsMargins(0, 0, 0, 0)

        self.interval_input = QLineEdit()
        self.interval_input.setObjectName("configInput")
        self.interval_input.setPlaceholderText("例如：5")
        interval_layout.addWidget(self.interval_input)

        interval_unit = QLabel("分钟")
        interval_unit.setObjectName("unitLabel")
        interval_layout.addWidget(interval_unit)
        interval_layout.addStretch()

        # 开机自启动设置
        self.startup_checkbox = QCheckBox("开机自启")
        self.startup_checkbox.setObjectName("configCheckbox")

        settings_layout.addRow("更新间隔:", interval_widget)
        settings_layout.addRow("", self.startup_checkbox)

        layout.addWidget(settings_group)

        # 保存按钮
        save_btn = QPushButton("保存设置")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_config)
        layout.addWidget(save_btn)
        layout.addStretch()

    def load_config(self):
        """加载保存的配置"""
        settings = self.config.get_settings()
        self.interval_input.setText(str(settings['interval']))
        self.startup_checkbox.setChecked(settings['startup'])

    def save_config(self):
        """保存设置"""
        try:
            interval = int(self.interval_input.text())
            if interval < 1 or interval > 1440:
                self.main_window.show_message("更新间隔必须在1-1440分钟之间", "error")
                return
        except ValueError:
            self.main_window.show_message("请输入有效的更新间隔", "error")
            return

        settings = {
            'interval': interval,
            'startup': self.startup_checkbox.isChecked()
        }

        self.config.save_settings(settings)
        self.load_config()

        if self.main_window and hasattr(self.main_window, 'status_tab'):
            self.main_window.status_tab.update_refresh_interval()
        self.main_window.show_message("设置已保存", "success")
