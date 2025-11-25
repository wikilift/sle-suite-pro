from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QTextCursor, QColor, QPalette
from PySide6.QtCore import QTimer, Qt


class LogPanel(QTextEdit):
    def __init__(self, is_dark=True):
        super().__init__()
        self.setReadOnly(True)
        self.setObjectName("logPanel")

        self._is_dark = None
        self.colors = {}
        self._apply_palette(is_dark)

    def _apply_palette(self, is_dark: bool):
        self._is_dark = is_dark

        palette = self.palette()
        if is_dark:
            palette.setColor(QPalette.Base, QColor("#000000"))
            palette.setColor(QPalette.Text, QColor("#00ff66"))
            self.colors = {
                "default": "#00ff66",
                "tx": "#4aa3ff",
                "rx": "#00ff66",
                "psc": "#ffa640",
                "error": "#ff3c3c",
            }
        else:
            palette.setColor(QPalette.Base, QColor("#1f1f1f"))
            palette.setColor(QPalette.Text, QColor("#e6e6e6"))
            self.colors = {
                "default": "#e6e6e6",
                "tx": "#6bb6ff",
                "rx": "#5cff89",
                "psc": "#ffb75a",
                "error": "#ff5c5c",
            }

        self.setPalette(palette)

    def set_dark_mode(self, is_dark: bool):
        if is_dark != self._is_dark:
            self._apply_palette(is_dark)

    def clear_log(self):
        self.clear()

    def log(self, msg: str):
        category = self._infer_category(msg)
        color_hex = self.colors.get(category, self.colors.get("default", "#ffffff"))
        self.setTextColor(QColor(color_hex))
        self.append(msg)
        self.setTextColor(QColor(self.colors.get("default", "#ffffff")))
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _infer_category(self, msg: str) -> str:
        m = msg.strip()
        if "Error" in m or "ERROR" in m:
            return "error"
        if m.startswith("<<"):
            return "tx"
        if m.startswith(">>") or "DATA" in m:
            return "rx"
        if "PSC" in m or "PIN" in m:
            return "psc"
        return "default"

    def _scroll_to_bottom(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and (event.modifiers() & Qt.ControlModifier):
            self.clear_log()
            return
        super().keyPressEvent(event)
