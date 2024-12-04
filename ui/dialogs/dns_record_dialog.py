import importlib

from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout,
                               QPushButton, QLineEdit, QComboBox,
                               QWidget, QGroupBox, QHBoxLayout, QMessageBox)

from dns_platforms import PLATFORM_NAMES, PLATFORM_MAPPING
from utils.logger import Logger


class DNSRecordDialog(QDialog):
    def __init__(self, parent=None, record_data=None):
        super().__init__(parent)
        self.parent = parent
        self.record_data = record_data
        self.logger = Logger()
        self.old_pos = None
        self._drag_pos = None

        # 初始化UI组件
        self.platform_combo = None
        self.record_type_combo = None
        self.platform_settings = None
        self.form_layout = None
        self.form_fields = {}

        # 设置窗口属性
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(500)

        self.setup_ui()

        # 如果是编辑模式，立即设置基本选项，然后延迟加载详细信息
        if self.record_data:
            self.init_basic_fields()
            QTimer.singleShot(50, self.init_platform_fields)  # 减少延迟时间

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 主容器
        main_widget = QWidget()
        main_widget.setObjectName("inner_widget")
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 表单区域
        form_group = QGroupBox()
        form_group.setObjectName("configCard")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # DNS平台选择
        self.platform_combo = QComboBox()
        self.platform_combo.setObjectName("configCombo")
        self.platform_combo.addItem("请选择DNS平台")
        self.platform_combo.addItems(PLATFORM_NAMES)
        self.platform_combo.currentTextChanged.connect(self.on_platform_changed)
        self.platform_combo.setFixedHeight(32)

        # 记录类型选择
        self.record_type_combo = QComboBox()
        self.record_type_combo.setObjectName("configCombo")
        self.record_type_combo.addItems(["A (IPv4)", "AAAA (IPv6)"])
        self.record_type_combo.setFixedHeight(32)

        # 添加基本设置
        form_layout.addRow("DNS平台:", self.platform_combo)
        form_layout.addRow("记录类型:", self.record_type_combo)

        # 创建平台特定设置容
        self.platform_settings = QWidget()
        self.form_layout = QFormLayout(self.platform_settings)
        self.form_layout.setSpacing(15)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.form_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        form_layout.addRow(self.platform_settings)

        main_layout.addWidget(form_group)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)

        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("primaryButton")
        cancel_btn.setProperty("delete", "true")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setFixedSize(100, 32)

        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("primaryButton")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setFixedSize(100, 32)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)

        main_layout.addLayout(button_layout)
        layout.addWidget(main_widget)

    def on_platform_changed(self, platform_name):
        """平台选择变化时更新表单"""
        # 先隐藏和清理平台设置
        self.platform_settings.hide()

        # 清理所有现有字段
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        self.form_fields.clear()

        if platform_name == "请选择DNS平台":
            return

        try:
            module_name = PLATFORM_MAPPING.get(platform_name)
            if not module_name:
                return

            module = importlib.import_module(f"dns_platforms.{module_name}")
            class_name = module_name.title() + 'DNS'
            platform_class = getattr(module, class_name)

            # 创建所有字段（除了域名字段）
            for field_name, field_config in platform_class.CONFIG_FIELDS.items():
                if field_name == 'domain':  # 域名字段最后处理
                    continue

                if field_name == 'hostname':  # 主机名使用文本输入框
                    input_field = QLineEdit()
                    input_field.setObjectName("configInput")
                    input_field.setPlaceholderText(field_config.get('placeholder', ''))
                    input_field.setFixedHeight(32)
                else:  # 其他认证字段
                    input_field = QLineEdit()
                    input_field.setObjectName("configInput")
                    input_field.setPlaceholderText(field_config.get('placeholder', ''))
                    input_field.setFixedHeight(32)

                # 如果是编辑模式且当前平台匹配，从record_data中获取值
                if (self.record_data and field_name in self.record_data and
                        self.record_data.get('platform') == platform_name):
                    input_field.setText(self.record_data[field_name])

                self.form_layout.addRow(field_config['label'] + ":", input_field)
                self.form_fields[field_name] = input_field

            # 最后创建域名字段
            if 'domain' in platform_class.CONFIG_FIELDS:
                field_config = platform_class.CONFIG_FIELDS['domain']
                # 为域名字段创建一个水平布局
                field_widget = QWidget()
                field_layout = QHBoxLayout(field_widget)
                field_layout.setContentsMargins(0, 0, 0, 0)
                field_layout.setSpacing(10)

                # 创建域名下拉框
                input_field = QComboBox()
                input_field.setObjectName("configCombo")
                input_field.setFixedHeight(32)

                # 果有认证信息，立即获取域名列表
                auth_fields = {}
                for field_name, field in self.form_fields.items():
                    if field_name != 'domain':  # 跳过域名字段
                        auth_fields[field_name] = field.text().strip()

                if all(auth_fields.values()):  # 如果所有认证字段都有值
                    try:
                        platform_instance = platform_class(auth_fields)
                        domains = platform_instance.get_domains()
                        if domains:
                            input_field.addItems(domains)
                    except Exception as e:
                        self.logger.error(f"获取域名列表失败: {str(e)}")

                field_layout.addWidget(input_field, 1)  # 添加拉伸因子1

                # 创建获取域名按钮
                fetch_btn = QPushButton("获取")
                fetch_btn.setObjectName("smallButton")
                fetch_btn.setFixedSize(60, 32)
                fetch_btn.clicked.connect(lambda: self._refresh_domains(platform_name, input_field))
                field_layout.addWidget(fetch_btn)

                self.form_layout.addRow(field_config['label'] + ":", field_widget)
                self.form_fields['domain'] = input_field

            self.platform_settings.show()

        except Exception as e:
            print(f"加载平台配置失败: {str(e)}")
            self.platform_settings.hide()

    def _refresh_domains(self, platform_name, domain_combo):
        """刷新域名列表"""
        try:
            # 获取平台类
            module_name = PLATFORM_MAPPING.get(platform_name)
            if not module_name:
                return

            module = importlib.import_module(f"dns_platforms.{module_name}")
            class_name = module_name.title() + 'DNS'
            platform_class = getattr(module, class_name)

            # 收集认证信息
            config = {}
            for field_name, field in self.form_fields.items():
                if field_name != 'domain':  # 跳过域名字段
                    if isinstance(field, QLineEdit):
                        value = field.text().strip()
                        if not value:  # 如果必要字段为空
                            QMessageBox.warning(self, "错误", "请填写所有必要的认证信息")
                            return
                        config[field_name] = value

            # 创建平台实例并获取域名列表
            try:
                platform_instance = platform_class(config)
                domains = platform_instance.get_domains()

                if not domains:
                    QMessageBox.warning(self, "提示", "未找到任何域名，请检查认证信息是否正确")
                    return

                # 更新域名下拉框
                domain_combo.clear()
                domain_combo.addItems(domains)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"获取域名列表失败: {str(e)}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"初始化DNS平台失败: {str(e)}")

    def mousePressEvent(self, event):
        """记录鼠标按下的位置"""
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        """处理拖动"""
        if not self.old_pos:
            return

        delta = QPoint(event.globalPos() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        """处理释放"""
        self.old_pos = None

    def init_basic_fields(self):
        """初始化基本字段（平台和记录类型）"""
        try:
            # 设置平台
            if 'platform' in self.record_data:
                platform = self.record_data['platform']
                index = self.platform_combo.findText(platform)
                if index >= 0:
                    self.platform_combo.setCurrentIndex(index)

            # 设置记录类型
            if 'record_type' in self.record_data:
                record_type = self.record_data['record_type']
                type_text = f"{record_type} - {'IPv4' if record_type == 'A' else 'IPv6'}"
                type_index = self.record_type_combo.findText(type_text)
                if type_index >= 0:
                    self.record_type_combo.setCurrentIndex(type_index)
        except Exception as e:
            self.logger.error(f"初始化基本字段失败: {str(e)}")

    def init_platform_fields(self):
        """初始化平台特定字段"""
        try:
            # 等待平台字段创建完成
            if not self.form_fields:
                QTimer.singleShot(50, self.init_platform_fields)
                return

            # 填充字段值
            for field_name, field in self.form_fields.items():
                if field_name in self.record_data:
                    if isinstance(field, QComboBox):
                        value = self.record_data[field_name]
                        index = field.findText(value)
                        if index >= 0:
                            field.setCurrentIndex(index)
                        else:
                            field.addItem(value)
                            field.setCurrentText(value)
                    elif isinstance(field, QLineEdit):
                        field.setText(self.record_data[field_name])
        except Exception as e:
            self.logger.error(f"初始化平台字段失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载记录数据失败: {str(e)}")

    def get_form_data(self):
        """获取表单数据"""
        data = {
            'platform': self.platform_combo.currentText(),
            'record_type': self.record_type_combo.currentText().split(' ')[0],
            'domain': self.form_fields.get('domain', '').currentText(),
            'hostname': self.form_fields.get('hostname', '').text() or '@',  # 如果为空则使用 @
        }

        # 获取平台特定的字段
        for field_name, field in self.form_fields.items():
            if field_name not in ['domain', 'hostname']:  # 已经添加过的字段跳过
                data[field_name] = field.text()

        return data
