from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPixmap

# 创建一个32x32的图标
icon = QPixmap(32, 32)
icon.fill(Qt.transparent)

painter = QPainter(icon)
painter.setRenderHint(QPainter.Antialiasing)

# 绘制一个圆形背景
painter.setBrush(QColor("#5352ed"))
painter.setPen(Qt.NoPen)
painter.drawEllipse(2, 2, 28, 28)

# 绘制文字
painter.setPen(QColor("white"))
font = painter.font()
font.setPointSize(14)
font.setBold(True)
painter.setFont(font)
painter.drawText(icon.rect(), Qt.AlignCenter, "D")

painter.end()

# 保存图标
icon.save("resources/icon.png")
