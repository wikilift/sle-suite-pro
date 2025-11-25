from PySide6.QtWidgets import QWidget, QGridLayout, QLineEdit, QLabel, QScrollArea, QVBoxLayout, QFrame
from PySide6.QtCore import Qt


class HexEditor(QWidget):
    def __init__(self):
        super().__init__()

        self.data = bytearray()
        self.cells = []
        self.ascii_rows = []
        self.offset_labels = []

        self.header_color = "#e8e8e8"
        self.changed_bg_color = "#c8ffda"
        self.cell_width = 42

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.inner = QWidget()
        self.grid = QGridLayout()
        self.grid.setSpacing(2)
        self.grid.setContentsMargins(6, 6, 6, 6)
        self.grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.inner.setLayout(self.grid)

        self.scroll.setWidget(self.inner)

        wrapper = QVBoxLayout()
        wrapper.addWidget(self.scroll)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setLayout(wrapper)

    def clear(self):
        for row in self.cells:
            for cell in row:
                cell.deleteLater()

        for line in self.ascii_rows:
            line.deleteLater()

        for lbl in self.offset_labels:
            lbl.deleteLater()

        self.cells.clear()
        self.ascii_rows.clear()
        self.offset_labels.clear()
        self.data = bytearray()

        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def load_data(self, data: bytes):
        self.clear()

        self.data = bytearray(data)
        total = len(self.data)

        header_style = f"font-weight: bold; background:{self.header_color};"

        offset_header = QLabel("Offset")
        offset_header.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        offset_header.setStyleSheet(header_style + " padding-right:6px;")
        offset_header.setFixedWidth(60)
        self.grid.addWidget(offset_header, 0, 0)

        for col in range(16):
            lbl = QLabel(f"{col:02X}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(header_style)
            lbl.setFixedWidth(self.cell_width)
            self.grid.addWidget(lbl, 0, col + 1)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #888888;")
        self.grid.addWidget(sep, 0, 17, 1, 1)

        ascii_header = QLabel("ASCII")
        ascii_header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        ascii_header.setStyleSheet(header_style + " padding-left:8px;")
        self.grid.addWidget(ascii_header, 0, 18)

        row = 1
        idx = 0

        while idx < total:
            offset_lbl = QLabel(f"{idx:04X}")
            offset_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            offset_lbl.setStyleSheet(header_style + " padding-right:6px;")
            offset_lbl.setFixedWidth(60)
            self.grid.addWidget(offset_lbl, row, 0)
            self.offset_labels.append(offset_lbl)

            row_cells = []

            for col in range(16):
                if idx >= total:
                    break

                val = self.data[idx]
                text = f"{val:02X}"

                cell = _HexCell(self, idx, text)
                cell.setAlignment(Qt.AlignCenter)
                cell.setFixedWidth(self.cell_width)
                cell.setMaxLength(2)
                cell.setStyleSheet("font-family: monospace;")
                self.grid.addWidget(cell, row, col + 1)
                row_cells.append(cell)

                idx += 1

            self.cells.append(row_cells)

            ascii_text = []
            base_index = (row - 1) * 16
            for col in range(16):
                byte_index = base_index + col
                if byte_index >= len(self.data):
                    break
                b = self.data[byte_index]
                ch = chr(b) if 32 <= b < 127 else "."
                ascii_text.append(ch)

            ascii_line = QLineEdit("".join(ascii_text))
            ascii_line.setReadOnly(True)
            ascii_line.setFrame(False)
            ascii_line.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            ascii_line.setStyleSheet(
                "font-family: monospace; padding-left:8px; background: transparent;"
            )
            self.grid.addWidget(ascii_line, row, 18)
            self.ascii_rows.append(ascii_line)

            row += 1

    def write_cell(self, index: int, new_text: str):
        row = index // 16
        col = index % 16

        try:
            cell = self.cells[row][col]
        except IndexError:
            return

        raw = new_text.strip()
        old_val = self.data[index] if index < len(self.data) else 0

        if raw == "":
            val = 0xFF
            normalized = "FF"
        else:
            try:
                val = int(raw, 16) & 0xFF
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
                f"font-weight: bold; "
                f"font-family: monospace;"
            )
        else:
            cell.setStyleSheet("font-family: monospace;")

        if index < len(self.data):
            self.data[index] = val

            try:
                ascii_line = self.ascii_rows[row]
            except IndexError:
                return

            ascii_chars = []
            base_index = row * 16
            for c in range(16):
                byte_index = base_index + c
                if byte_index >= len(self.data):
                    break
                b = self.data[byte_index]
                ch = chr(b) if 32 <= b < 127 else "."
                ascii_chars.append(ch)

            ascii_line.setText("".join(ascii_chars))

    def get_bytes(self) -> bytes:
        return bytes(self.data)

    def commit_all(self):
        for row_idx, row in enumerate(self.cells):
            for col_idx, cell in enumerate(row):
                index = row_idx * 16 + col_idx
                if index >= len(self.data):
                    break
                self.write_cell(index, cell.text())


class _HexCell(QLineEdit):
    def __init__(self, editor: HexEditor, index: int, text: str):
        super().__init__(text)
        self.editor = editor
        self.index = index

    def focusOutEvent(self, event):
        self.editor.write_cell(self.index, self.text())
        super().focusOutEvent(event)
