from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QPoint, QEasingCurve
from PySide6.QtGui import QEnterEvent


class ClickableLabel(QLabel):
    clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setCursor(Qt.PointingHandCursor)

        self.hover_anim = QPropertyAnimation(self, b"geometry")
        self.hover_anim.setDuration(140)
        self.hover_anim.setEasingCurve(QEasingCurve.OutQuad)

        self.click_anim = QPropertyAnimation(self, b"geometry")
        self.click_anim.setDuration(110)
        self.click_anim.setEasingCurve(QEasingCurve.InOutQuad)

    def enterEvent(self, event: QEnterEvent):
        g = self.geometry()
        self.hover_anim.stop()
        self.hover_anim.setStartValue(g)
        self.hover_anim.setEndValue(g.adjusted(-4, -4, 4, 4))
        self.hover_anim.start()

    def leaveEvent(self, event):
        g = self.geometry()
        self.hover_anim.stop()
        self.hover_anim.setStartValue(g)
        self.hover_anim.setEndValue(g.adjusted(4, 4, -4, -4))
        self.hover_anim.start()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            g = self.geometry()
            self.click_anim.stop()
            self.click_anim.setStartValue(g)
            self.click_anim.setEndValue(g.adjusted(3, 3, -3, -3))
            self.click_anim.start()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.clicked.emit()
            g = self.geometry()
            self.click_anim.stop()
            self.click_anim.setStartValue(g)
            self.click_anim.setEndValue(g.adjusted(-3, -3, 3, 3))
            self.click_anim.start()
