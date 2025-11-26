from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QFrame, QPushButton, QHBoxLayout, QSizePolicy
)
from PySide6.QtGui import QPixmap, QPainter, QPainterPath
from PySide6.QtCore import Qt
import webbrowser
from core.resource import resource_path
from gui.widgets.clickable_label import ClickableLabel


def rounded_pixmap(pixmap, radius=24):
    w = pixmap.width()
    h = pixmap.height()

    result = QPixmap(w, h)
    result.fill(Qt.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing, True)

    path = QPainterPath()
    path.addRoundedRect(0, 0, w, h, radius, radius)

    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()

    return result


class AboutDialog(QDialog):
    def __init__(self, parent=None, tr=lambda s: s):
        super().__init__(parent)

        self.setWindowTitle("SLE Suite PRO")
        self.setMinimumWidth(540)

        main = QVBoxLayout(self)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(16)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(255,255,255,0.08);
                border-radius: 16px;
                padding: 30px;
            }
        """)

        container.setGraphicsEffect(self._shadow())

        v = QVBoxLayout(container)
        v.setAlignment(Qt.AlignCenter)
        v.setSpacing(20)

        title = QLabel("SLE Suite PRO")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        v.addWidget(title)

        subtitle = QLabel("(c) 2025 Wikilift")
        subtitle.setStyleSheet("font-size: 14px; color: gray;")
        v.addWidget(subtitle)

        txt = QLabel(tr("msg.support_text"))
        txt.setWordWrap(True)
        txt.setAlignment(Qt.AlignCenter)
        txt.setStyleSheet("font-size: 17px; padding: 6px;")
        txt.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        txt.setMinimumWidth(420)
        v.addWidget(txt)

        github = QLabel(
            "<a href='https://github.com/wikilift'>Meet me on GitHub: Wikilift</a>"
        )
        github.setOpenExternalLinks(True)
        github.setAlignment(Qt.AlignCenter)
        github.setStyleSheet("font-size: 15px;")
        v.addWidget(github)

        pix = QPixmap(resource_path("assets/coffee.svg")).scaledToWidth(260, Qt.SmoothTransformation)
        pix = rounded_pixmap(pix, radius=40)

        img = ClickableLabel()
        img.setPixmap(pix)
        img.clicked.connect(lambda: webbrowser.open("https://buymeacoffee.com/wikilift"))
        v.addWidget(img)

        main.addWidget(container, alignment=Qt.AlignCenter)

        btn_close = QPushButton(tr("menu.exit"))
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        btn_close.clicked.connect(self.accept)

        main.addWidget(btn_close, alignment=Qt.AlignCenter)


    def _shadow(self):
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 6)
        shadow.setColor(Qt.black)
        return shadow
