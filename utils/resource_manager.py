from pathlib import Path
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtCore import QSize, Qt
from PySide6.QtSvg import QSvgRenderer
import io
import sys
import os


class ResourceManager:
    @staticmethod
    def svg_to_pixmap(svg_path, size):
        """将SVG转换为指定大小的QPixmap"""
        renderer = QSvgRenderer(str(svg_path))
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap

    @staticmethod
    def get_icon(name):
        """获取图标资源"""
        resource_dir = Path(__file__).parent.parent / 'resources'
        icon_path = resource_dir / name

        if icon_path.exists():
            if name.endswith('.svg'):
                # 创建多尺寸图标
                icon = QIcon()
                sizes = [16, 24, 32, 48, 64, 128]  # Windows常用尺寸
                for size in sizes:
                    qsize = QSize(size, size)
                    pixmap = ResourceManager.svg_to_pixmap(icon_path, qsize)
                    icon.addPixmap(pixmap)
                return icon
            else:
                return QIcon(str(icon_path))
        return QIcon()

    @staticmethod
    def get_resource_path(name):
        """获取资源文件路径"""
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            base_path = sys._MEIPASS
        else:
            # 如果是开发环境
            base_path = os.path.dirname(os.path.dirname(__file__))

        return os.path.join(base_path, 'resources', name)