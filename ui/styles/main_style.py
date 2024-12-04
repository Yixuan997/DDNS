class MainStyle:
    @staticmethod
    def get_style():
        return """
            QMainWindow {
                background: transparent;
            }

            #central_widget {
                background: transparent;
            }

            #inner_widget {
                background-color: #f5f6fa;
                border-radius: 10px;
                border: 1px solid #e1e5ee;
            }

            #content_widget {
                background-color: #f5f6fa;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }

            #titleBar {
                background-color: transparent;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                height: 35px;
            }

            QTabWidget::pane {
                border: none;
                background: #ffffff;
                border-radius: 10px;
                margin-top: 10px;
            }

            QTabBar {
                background: transparent;
            }

            QTabBar::tab {
                padding: 8px 20px;
                margin-right: 5px;
                border: none;
                background: #e1e5ee;
                border-radius: 5px;
                color: #2f3542;
                min-width: 80px;
                font-weight: 500;
            }

            QTabBar::tab:selected {
                background: #5352ed;
                color: white;
            }

            QTabBar::tab:hover:!selected {
                background: #d1d5ee;
            }

            QTabWidget QWidget {
                margin: 0;
            }

            QTabWidget QScrollArea {
                border: none;
                background: transparent;
            }

            QTabWidget > QWidget {
                margin: 2px;
            }

            #statusCard, #configCard {
                background: white;
            }

            #titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2f3542;
                padding: 10px 0;
            }

            #windowTitle {
                color: #2f3542;
                font-weight: bold;
                font-size: 12px;
            }

            #minButton, #maxButton, #closeButton {
                background: transparent;
                border: none;
                color: #2f3542;
                font-size: 16px;
                padding: 5px 10px;
                font-family: "Segoe UI Symbol", sans-serif;
            }

            #minButton:hover, #maxButton:hover {
                background: rgba(0, 0, 0, 0.1);
            }

            #closeButton:hover {
                background: #ff4757;
                color: white;
            }

            QGroupBox {
                background-color: white;
                border: 2px solid #e1e5ee;
                border-radius: 10px;
                padding: 15px;
                margin-top: 10px;
                font-weight: bold;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 5px;
                color: #2f3542;
            }

            #ipLabel {
                font-weight: bold;
                color: #2f3542;
                min-width: 60px;
            }

            #ipValue {
                color: #5352ed;
                font-family: monospace;
            }

            #configInput {
                padding: 8px;
                border: 2px solid #e1e5ee;
                border-radius: 5px;
                background: white;
            }

            #configInput:focus {
                border-color: #5352ed;
            }

            #configCombo {
                padding: 8px;
                border: 2px solid #e1e5ee;
                border-radius: 5px;
                background: white;
                min-width: 150px;
            }

            #configCombo:focus {
                border-color: #5352ed;
            }

            #configCombo::drop-down {
                border: none;
                width: 30px;
                border-left: 2px solid transparent;
            }

            #configCombo::down-arrow {
                width: 10px;
                height: 10px;
                margin-right: 12px;
                image: url(resources/arrow-down.svg);
            }

            #primaryButton {
                background: #5352ed;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 100px;
            }

            #primaryButton:hover {
                background: #3432db;
            }

            #primaryButton:pressed {
                background: #2826b5;
                padding: 11px 20px 9px 20px;
            }

            #configCheckbox {
                color: #2f3542;
            }

            #unitLabel {
                color: #2f3542;
                margin-left: 5px;
                font-size: 14px;
            }

            #container {
                background-color: white;
                border-radius: 8px;
                border: 1px solid rgba(0, 0, 0, 0.1);
                min-width: 120px;
            }

            #statusIndicator {
                font-size: 16px;
                padding-right: 5px;
            }

            #lastUpdateLabel {
                color: #666;
                font-size: 12px;
                margin-top: 5px;
            }

            #logText {
                background: white;
                border: 2px solid #e1e5ee;
                border-radius: 10px;
                padding: 10px;
                font-family: monospace;
                font-size: 13px;
                line-height: 1.5;
            }

            #logText:focus {
                border-color: #5352ed;
            }

            #recordsTable {
                background: white;
                border: none;
            }

            #recordsTable::item {
                padding: 8px;
                text-align: center;
            }

            #recordsTable QHeaderView::section {
                background-color: #f5f6fa;
                padding: 8px;
                border: none;
                font-weight: bold;
                color: #2f3542;
                text-align: center;
            }

            #recordsTable QHeaderView::section:first {
                width: 150px;  /* 平台列宽 */
            }

            #recordsTable QHeaderView::section:nth-child(2) {
                width: 150px;  /* 域名列宽 */
            }

            #recordsTable QHeaderView::section:last {
                width: 150px;  /* 主机名列宽 */
            }

            #smallButton {
                background-color: #5352ed;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 3px;
                font-size: 12px;
                min-width: 50px;
                margin: 2px;
            }

            #smallButton:hover {
                background-color: #3432db;
            }

            #smallButton[delete="true"] {
                background-color: #e74c3c;
                color: white;
            }

            #smallButton[delete="true"]:hover {
                background-color: #c0392b;
            }

            QDialog {
                background: transparent;
            }

            QDialog #inner_widget {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e1e5ee;
            }

            QDialog::backdrop {
                background-color: transparent;
            }

            QDialog #configCard {
                background-color: white;
                border: 2px solid #e1e5ee;
                border-radius: 10px;
                padding: 15px;
            }

            QDialog QLabel {
                color: #2f3542;
                font-weight: bold;
            }

            QDialog #configCombo {
                padding: 8px;
                border: 2px solid #e1e5ee;
                border-radius: 5px;
                background: white;
                min-width: 150px;
            }

            QDialog #configInput {
                padding: 8px;
                border: 2px solid #e1e5ee;
                border-radius: 5px;
                background: white;
            }

            QDialog #configCombo:focus, QDialog #configInput:focus {
                border-color: #5352ed;
            }

            #messageLabel {
                color: #2f3542;
                font-size: 14px;
                padding: 10px;
                background: white;
                border-radius: 5px;
            }
        """
