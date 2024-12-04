import os
import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from loguru import logger


class ResourceManager:
    @staticmethod
    def svg_to_pixmap(svg_path, size):
        """将SVG转换为指定大小的QPixmap"""
        try:
            renderer = QSvgRenderer(str(svg_path))
            pixmap = QPixmap(size)
            pixmap.fill(Qt.transparent)
            with QPainter(pixmap) as painter:
                renderer.render(painter)
            return pixmap
        except Exception as e:
            logger.error(f"SVG转换失败: {str(e)}")
            return QPixmap(size)

    @staticmethod
    def get_icon(name):
        """获取图标资源"""
        try:
            resource_dir = Path(__file__).parent.parent / 'resources'
            icon_path = resource_dir / name

            if not icon_path.exists():
                logger.warning(f"图标文件不存在: {icon_path}")
                return QIcon()

            if name.endswith('.svg'):
                icon = QIcon()
                sizes = [16, 24, 32, 48, 64, 128]
                for size in sizes:
                    qsize = QSize(size, size)
                    pixmap = ResourceManager.svg_to_pixmap(icon_path, qsize)
                    if not pixmap.isNull():
                        icon.addPixmap(pixmap)
                return icon
            return QIcon(str(icon_path))
        except Exception as e:
            logger.error(f"获取图标失败: {str(e)}")
            return QIcon()

    @staticmethod
    def get_resource_path(name):
        """获取资源文件路径"""
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.dirname(__file__))

            path = os.path.join(base_path, 'resources', name)
            if not os.path.exists(path):
                logger.warning(f"资源文件不存在: {path}")
            return path
        except Exception as e:
            logger.error(f"获取资源路径失败: {str(e)}")
            return name
