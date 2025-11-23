                          

from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QTextCursor, QColor
from PySide6.QtCore import QTimer


class LogPanel(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMaximumHeight(160)

                               
        self.colors = {
            "default": None,                                              
            "tx": "#1e90ff",                                       
            "rx": "#32cd32",                                          
            "psc": "#ff8c00",                             
            "error": "#ff4d4d",                      
        }

                                                               
    def log(self, msg: str):
   
        category = self._infer_category(msg)
        color_hex = self.colors.get(category)

                                                         
        default_color = self.textColor()

        if color_hex:
            self.setTextColor(QColor(color_hex))
        else:
                                          
            self.setTextColor(default_color)

                      
        self.append(msg)

                                     
        self.setTextColor(default_color)

                                                         
        QTimer.singleShot(0, self._scroll_to_bottom)

                                                               
    def _infer_category(self, msg: str) -> str:

        m = msg.strip()

                            
        if "Error" in m or "ERROR" in m:
            return "error"

        if m.startswith("<<"):
                                             
            return "tx"

        if m.startswith(">>") or m.startswith("DATA") or m.startswith(">> DATA"):
                                             
            return "rx"

        if "PSC" in m or "PIN" in m:
            return "psc"

        return "default"

                                                               
    def _scroll_to_bottom(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())
