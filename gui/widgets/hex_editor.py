                           

from PySide6.QtWidgets import QWidget, QGridLayout, QLineEdit, QLabel, QScrollArea, QVBoxLayout
from PySide6.QtCore import Qt


class HexEditor(QWidget):

    def __init__(self):
        super().__init__()

        self.data = bytearray()
        self.cells = []
        self.offset_labels = []
        self.ascii_mode = False

                         
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.inner = QWidget()
        self.grid = QGridLayout()
        self.grid.setSpacing(3)
        self.grid.setContentsMargins(6, 6, 6, 6)
        self.grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.inner.setLayout(self.grid)

        self.scroll.setWidget(self.inner)

        wrapper = QVBoxLayout()
        wrapper.addWidget(self.scroll)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setLayout(wrapper)

        self.header_color = "#e8e8e8"
        self.changed_bg_color = "#c8ffda"                 
        self.cell_width = 42

                                                             
    def clear(self):
        for row in self.cells:
            for cell in row:
                cell.deleteLater()

        for lbl in self.offset_labels:
            lbl.deleteLater()

        self.cells.clear()
        self.offset_labels.clear()
        self.data = bytearray()

        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w:
                w.deleteLater()

                                                             
    def load_data(self, data: bytes):
        self.clear()

        self.data = bytearray(data)
        total = len(self.data)

        header_style = f"font-weight: bold; background:{self.header_color};"

                    
        for col in range(16):
            lbl = QLabel(f"{col:02X}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(header_style)
            lbl.setFixedWidth(self.cell_width)
            self.grid.addWidget(lbl, 0, col + 1)

              
        row = 1
        idx = 0

        while idx < total:

            offset_lbl = QLabel(f"{idx:04X}")
            offset_lbl.setAlignment(Qt.AlignRight)
            offset_lbl.setStyleSheet(header_style + " padding-right:6px;")
            offset_lbl.setFixedWidth(60)
            self.grid.addWidget(offset_lbl, row, 0)
            self.offset_labels.append(offset_lbl)

            row_cells = []

            for col in range(16):
                if idx >= total:
                    break

                v = self.data[idx]
                text = f"{v:02X}"

                cell = _HexCell(self, idx, text)
                cell.setAlignment(Qt.AlignCenter)
                cell.setFixedWidth(self.cell_width)
                cell.setMaxLength(2)

                self.grid.addWidget(cell, row, col + 1)
                row_cells.append(cell)

                idx += 1

            self.cells.append(row_cells)
            row += 1

                                                             
    def write_cell(self, index, new_text):
      
        r = index // 16
        c = index % 16

        try:
            cell = self.cells[r][c]
        except IndexError:
            return

        raw = new_text.strip()
        old_val = self.data[index] if index < len(self.data) else 0

                                    
        if raw == "":
            val = 0xFF
            normalized = "FF"
        else:
            try:
                val = int(raw, 16)
                val &= 0xFF
                normalized = f"{val:02X}"
            except ValueError:
                val = 0xFF
                normalized = "FF"

                                            
        cell.blockSignals(True)
        cell.setText(normalized)
        cell.blockSignals(False)

                              
        if val != old_val:
            cell.setStyleSheet(
                f"background-color: {self.changed_bg_color}; "
                f"color: black; "
                f"font-weight: bold;"
            )
        else:
                                    
            cell.setStyleSheet("")

                                
        if index < len(self.data):
            self.data[index] = val

                                                             
    def set_view_ascii(self, enable: bool):
      
        self.ascii_mode = enable

        idx = 0
        for row in self.cells:
            for cell in row:
                if idx >= len(self.data):
                    break
                if enable:
                    b = self.data[idx]
                    cell.setText(chr(b) if 32 <= b < 127 else ".")
                else:
                    cell.setText(f"{self.data[idx]:02X}")
                idx += 1

                                                             
    def get_bytes(self):
        return bytes(self.data)


                                                         
                                
                                                         
class _HexCell(QLineEdit):

    def __init__(self, editor, index, text):
        super().__init__(text)
        self.editor = editor
        self.index = index

    def focusOutEvent(self, event):
       
        self.editor.write_cell(self.index, self.text())
        super().focusOutEvent(event)
