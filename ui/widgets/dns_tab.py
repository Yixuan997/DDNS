import importlib
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLineEdit, QGroupBox, QTableWidget, QTableWidgetItem,
                               QHBoxLayout,
                               QHeaderView)

from dns_platforms import PLATFORM_MAPPING
from ui.dialogs.dns_record_dialog import DNSRecordDialog
from utils.logger import Logger


class DNSTab(QWidget):
    def __init__(self, config, main_window=None):
        super().__init__()
        self.config = config
        self.main_window = main_window
        self.editing_row = None
        self.form_fields = {}  # 存储动态创建的表单字段
        self.logger = Logger()
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # DNS记录列表区域
        records_group = QGroupBox("DNS记录列表")
        records_group.setObjectName("configCard")
        records_layout = QVBoxLayout(records_group)
        records_layout.setSpacing(15)

        # 记录表格
        self.records_table = QTableWidget()
        self.records_table.setObjectName("recordsTable")
        self.setup_records_table()
        self.records_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.records_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.records_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.records_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.records_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.records_table.setSelectionMode(QTableWidget.SingleSelection)
        self.records_table.verticalHeader().setVisible(False)
        self.records_table.setEditTriggers(QTableWidget.NoEditTriggers)
        records_layout.addWidget(self.records_table)

        # 添加记录列表到主布局
        layout.addWidget(records_group)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)

        # 添加记录按钮
        self.add_btn = QPushButton("添加")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.setFixedWidth(60)  # 设置固定宽度
        self.add_btn.clicked.connect(self.add_record)

        # 编辑记录按钮
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.setObjectName("primaryButton")
        self.edit_btn.setFixedWidth(60)  # 设置固定宽度
        self.edit_btn.clicked.connect(self.edit_selected_record)
        self.edit_btn.setVisible(False)  # 初始隐藏

        # 删除记录按钮
        self.delete_btn = QPushButton("删除")
        self.delete_btn.setObjectName("primaryButton")
        self.delete_btn.setProperty("delete", "true")
        self.delete_btn.setFixedWidth(60)  # 设置固定宽度
        self.delete_btn.clicked.connect(self.delete_selected_record)
        self.delete_btn.setVisible(False)  # 初始隐藏

        button_layout.addWidget(self.add_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)

        # 添加按钮到主布局
        layout.addLayout(button_layout)

        # 选择变化时启用/禁用按钮
        self.records_table.itemSelectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self):
        """选择行变化时的处理"""
        has_selection = bool(self.records_table.selectedItems())
        self.edit_btn.setVisible(has_selection)
        self.delete_btn.setVisible(has_selection)

    def edit_selected_record(self):
        """编辑选中的记录"""
        selected_rows = self.records_table.selectedItems()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        platform = self.records_table.item(row, 0).text()
        domain = self.records_table.item(row, 1).text()
        hostname = self.records_table.item(row, 2).text()

        # 获取平台模块名
        platform_module = PLATFORM_MAPPING.get(platform)
        if not platform_module:
            self.logger.error(f"不支持的DNS平台: {platform}")
            return

        # 从配置中获取完整记录数据
        config = self.config.load_config()
        platforms = config.get('platforms', {})
        records = platforms.get(platform_module, [])

        # 查找匹配的记录
        record_data = None
        for record in records:
            if record.get('domain') == domain and record.get('hostname', '@') == hostname:
                record_data = record.copy()
                record_data['platform'] = platform
                break

        if record_data:
            dialog = DNSRecordDialog(self, record_data)
            if dialog.exec():
                # 获取新的表单数据
                form_data = dialog.get_form_data()

                # 更新配置
                config = self.config.load_config()
                platforms = config.get('platforms', {})
                records = platforms.get(platform_module, [])

                # 更新匹配的记录
                for i, record in enumerate(records):
                    if record.get('domain') == domain and record.get('hostname', '@') == hostname:
                        records[i] = form_data
                        break

                # 保存配置
                config['platforms'][platform_module] = records
                self.config.save_config(config)

                # 刷新显示
                self.refresh_records()

                # 显示成功消息
                if self.main_window:
                    self.main_window.show_message("DNS记录已更新", "success")

    def delete_selected_record(self):
        """删除选中的记录"""
        selected_rows = self.records_table.selectedItems()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        self.delete_record(row)

    def load_record_to_form(self, row):
        """加载记录到表单"""
        platform = self.records_table.item(row, 0).text()
        record_type = self.records_table.item(row, 1).text()

        # 设置平台和记录类型
        platform_index = self.platform_combo.findText(platform)
        if platform_index >= 0:
            self.platform_combo.setCurrentIndex(platform_index)

        record_type_index = self.record_type_combo.findText(record_type)
        if record_type_index >= 0:
            self.record_type_combo.setCurrentIndex(record_type_index)

        # 获取完整配置
        record_config = self.get_record_config(row)
        if record_config:
            # 设置表单字段的值
            for field_name, field in self.form_fields.items():
                field.setText(record_config.get(field_name, ''))

    def clear_form(self):
        """清空表单"""
        self.form_fields.clear()  # 清空字段字典

        # 重置选择框
        if self.platform_combo.count() > 0:
            self.platform_combo.setCurrentIndex(0)
        if self.record_type_combo.count() > 0:
            self.record_type_combo.setCurrentIndex(0)

    def save_record(self):
        """保存修改"""
        if self.editing_row is None:
            return

        # 获取表单数据
        form_data = self.get_form_data()

        # 验证填字段
        if not form_data.get('domain'):
            self.main_window.show_message("请输入域名", "error")
            return

        # 更新表格内容
        self.records_table.setItem(self.editing_row, 0, QTableWidgetItem(self.platform_combo.currentText()))
        self.records_table.setItem(self.editing_row, 1, QTableWidgetItem(self.record_type_combo.currentText()))
        self.records_table.setItem(self.editing_row, 2, QTableWidgetItem(form_data.get('domain', '')))

        # 保存配置
        self.save_config()

        # 清空表单
        self.clear_form()
        self.editing_row = None

        # 更新按钮状态
        self.save_btn.setVisible(False)
        self.delete_btn.setVisible(False)

        # 取消选择
        self.records_table.clearSelection()

        self.main_window.show_message("DNS记录已更新", "success")

    def add_record(self):
        """添加新记录"""
        dialog = DNSRecordDialog(self)
        if dialog.exec():
            form_data = dialog.get_form_data()

            # 获取平台模块名
            platform_name = form_data['platform']
            platform_module = PLATFORM_MAPPING.get(platform_name)

            if not platform_module:
                self.logger.error(f"不支持的DNS平台: {platform_name}")
                return

            # 更新配置
            config = self.config.load_config()
            if 'platforms' not in config:
                config['platforms'] = {}

            if platform_module not in config['platforms']:
                config['platforms'][platform_module] = []

            # 添加记录
            config['platforms'][platform_module].append(form_data)

            # 保存配置
            self.config.save_config(config)

            # 刷新显示
            self.refresh_records()

            # 显示成功消息
            if self.main_window:
                self.main_window.show_message("DNS记录已添加", "success")

    def edit_record(self, record_data):
        """编辑现有记录"""
        dialog = DNSRecordDialog(self, record_data)
        if dialog.exec():
            self.refresh_records()

    def delete_record(self, row):
        """删除记录"""
        # 使用对话框请求确认
        if self.main_window.show_dialog("确定删除这条DNS记录吗？", "confirm"):
            self.records_table.removeRow(row)
            self.save_config()
            # 使Toast显示成功消息
            self.main_window.show_message("DNS记录已删除", "success")

    def load_config(self):
        """加载配置到表格"""
        config = self.config.load_config()
        platforms = config.get('platforms', {})

        # 清空表格
        self.records_table.setRowCount(0)

        # 添加记录到表格
        for platform_name, records in platforms.items():
            if isinstance(records, list):
                for record in records:
                    self._add_record_to_table(platform_name, record)
            else:
                self._add_record_to_table(platform_name, records)

    def _add_record_to_table(self, platform_name, record):
        """添加单条记录到表格"""
        row = self.records_table.rowCount()
        self.records_table.insertRow(row)

        # 平台名称首字母大写
        display_name = platform_name.replace('_', ' ').title()

        # 设置表格内容并居中对齐
        for col, text in enumerate([
            display_name,
            record.get('domain', ''),
            record.get('hostname', '@')
        ]):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)  # 设置文本居中对齐
            self.records_table.setItem(row, col, item)

    def save_config(self):
        """保存DNS配置"""
        config = self.config.load_config()
        new_platforms = {}

        # 遍历表格中的所有记录
        for row in range(self.records_table.rowCount()):
            platform_name = self.records_table.item(row, 0).text()
            record_type = self.records_table.item(row, 1).text().split(' ')[0]
            domain = self.records_table.item(row, 2).text()

            # 获取平台模块名
            platform_module = PLATFORM_MAPPING.get(platform_name)
            if not platform_module:
                continue  # 跳过不支持的平台

            # 确保平台配置是列表
            if platform_module not in new_platforms:
                new_platforms[platform_module] = []

            # 从现有配置中获取认证信息
            record_config = {
                'domain': domain,
                'record_type': record_type
            }

            # 查找并保留认证信息
            if platform_module in config.get('platforms', {}):
                old_records = config['platforms'][platform_module]
                if isinstance(old_records, list):
                    for old_record in old_records:
                        if old_record.get('domain') == domain:
                            # 获取平台的配置字段
                            try:
                                module = importlib.import_module(f"dns_platforms.{platform_module}")
                                platform_class = getattr(module, f"{platform_module.title()}DNS")
                                # 保留所有平台特定的字段
                                for field in platform_class.CONFIG_FIELDS:
                                    if field != 'domain':  # 域名已经有了
                                        record_config[field] = old_record.get(field, '')
                            except Exception:
                                pass  # 如果获取平台配置失败，跳过
                            break
                elif isinstance(old_records, dict):
                    if old_records.get('domain') == domain:
                        try:
                            module = importlib.import_module(f"dns_platforms.{platform_module}")
                            platform_class = getattr(module, f"{platform_module.title()}DNS")
                            # 保留所���平台特定的字段
                            for field in platform_class.CONFIG_FIELDS:
                                if field != 'domain':  # 域名已经有了
                                    record_config[field] = old_records.get(field, '')
                        except Exception:
                            pass  # 如果获取平台配置失败，跳过

            # 添加记录到新配置
            new_platforms[platform_module].append(record_config)

        # 更新配置
        config['platforms'] = new_platforms
        self.config.save_config(config)

    def get_record_config(self, row):
        """获取完整的记录配置（包括明文API Token）"""
        platform = self.records_table.item(row, 0).text().lower().replace(' ', '_')
        config = self.config.load_config()
        platforms = config.get('platforms', {})
        records = platforms.get(platform, [])

        # 找到对应的记录
        domain = self.records_table.item(row, 1).text()
        for record in records:
            if record.get('domain') == domain:
                return record
        return None

    def load_available_platforms(self):
        """加载可用的DNS平台"""
        try:
            platforms_dir = Path(__file__).parent.parent.parent / 'dns_platforms'
            for file in platforms_dir.glob('*.py'):
                if file.stem not in ['__init__', 'base', 'aliyun']:  # 暂时排除aliyun
                    platform_name = file.stem.title()
                    self.platform_combo.addItem(platform_name)
        except Exception as e:
            self.logger.error(f"载DNS平台列表失败: {str(e)}")

    def on_platform_changed(self, platform_name):
        """平台选择变化时更新表单"""
        if platform_name == "请选择DNS平台":
            self.platform_settings.hide()
            return

        try:
            # 从映射获取模块名
            module_name = PLATFORM_MAPPING.get(platform_name)
            if not module_name:
                return

            # 动态加载平台类
            module = importlib.import_module(f"dns_platforms.{module_name}")
            class_name = module_name.title() + 'DNS'  # 使用模块名构造类名
            platform_class = getattr(module, class_name)

            # 保存当前表单的值
            current_values = {}
            for field_name, field in self.form_fields.items():
                current_values[field_name] = field.text()

            # 移除旧的表单字段
            for field_name, field in self.form_fields.items():
                row = self.form_layout.getWidgetPosition(field)[0]
                if row >= 0:
                    self.form_layout.removeRow(row)

            # 清空字段字典
            self.form_fields.clear()

            # 创建表单字段
            for field_name, field_config in platform_class.CONFIG_FIELDS.items():
                input_field = QLineEdit()
                input_field.setObjectName("configInput")
                input_field.setPlaceholderText(field_config.get('placeholder', ''))
                if field_config.get('password', False):
                    input_field.setEchoMode(QLineEdit.Password)

                # 如果有之前的值，保留它
                if field_name in current_values:
                    input_field.setText(current_values[field_name])

                # 添加到布局
                self.form_layout.addRow(field_config['label'] + ":", input_field)

                # 存到字段字典
                self.form_fields[field_name] = input_field

            self.platform_settings.show()

        except Exception as e:
            self.logger.error(f"加载平台配置失败: {str(e)}")

    def get_form_data(self):
        """获取表单数据"""
        data = {
            'platform': self.platform_combo.currentText().lower(),
            'record_type': self.record_type_combo.currentText().split(' ')[0]
        }
        for field_name, field in self.form_fields.items():
            data[field_name] = field.text()
        return data

    def set_form_data(self, data):
        """设置表单数据"""
        platform = data.get('platform', '').title()
        if platform:
            index = self.platform_combo.findText(platform)
            if index >= 0:
                self.platform_combo.setCurrentIndex(index)

        for field_name, value in data.items():
            if field_name in self.form_fields:
                self.form_fields[field_name].setText(value)

    def setup_records_table(self):
        """设置记录表格"""
        self.records_table.setObjectName("recordsTable")  # 确保设置了对象名
        self.records_table.setColumnCount(3)
        self.records_table.setHorizontalHeaderLabels([
            "平台",
            "域名",
            "主机名"
        ])

        # 设置列宽
        header = self.records_table.horizontalHeader()
        header.setDefaultSectionSize(150)  # 默认列宽

        # 禁止用户调整列宽
        header.setSectionResizeMode(QHeaderView.Fixed)

        # 设置表格其他属性
        self.records_table.setShowGrid(False)  # 不显示网格线
        self.records_table.setAlternatingRowColors(True)  # 交替行颜色
        self.records_table.verticalHeader().setVisible(False)  # 隐藏行号

    def refresh_records(self):
        """刷新DNS记录列表"""
        try:
            # 清空表格
            self.records_table.setRowCount(0)

            # 重新加载配置
            config = self.config.load_config()
            platforms = config.get('platforms', {})

            # 添加记录到表格
            for platform_name, records in platforms.items():
                if isinstance(records, list):
                    for record in records:
                        self._add_record_to_table(platform_name, record)
                else:
                    self._add_record_to_table(platform_name, records)

            # 更新按钮状态
            self.on_selection_changed()

        except Exception as e:
            self.logger.error(f"刷新DNS记录列表失败: {str(e)}")
            if self.main_window:
                self.main_window.show_message("刷新DNS记录列表失败", "error")
