from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QGridLayout, QCheckBox, QPushButton, QLabel, QMessageBox
)
from PySide6.QtCore import Qt
from core.language_manager import tr


class TabProtection(QWidget):
    def __init__(self, main):
        super().__init__()
        self.setObjectName("protectionPanel")

        self.main = main
        self.card = None
        self.checks = []
        self.original_bits = []

        root = QVBoxLayout()
        root.setAlignment(Qt.AlignTop)
        self.setLayout(root)

        top = QHBoxLayout()
        self.lbl_info = QLabel("")
        top.addWidget(self.lbl_info)
        top.addStretch()

        self.btn_reload = QPushButton(tr("btn.reload"))
        self.btn_reload.clicked.connect(self.reload)
        top.addWidget(self.btn_reload)

        self.btn_apply = QPushButton(tr("btn.write_protection"))
        self.btn_apply.clicked.connect(self.apply_changes)
        top.addWidget(self.btn_apply)

        root.addLayout(top)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        root.addWidget(self.scroll)

        self.container = QWidget()
        self.container.setObjectName("protectionGrid")

        self.grid = QGridLayout()
        self.grid.setContentsMargins(4, 4, 4, 4)
        self.grid.setHorizontalSpacing(3)
        self.grid.setVerticalSpacing(3)
        self.grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.container.setLayout(self.grid)
        self.scroll.setWidget(self.container)

    def clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.checks = []

    def load_from_card(self, card):
        self.card = card
        self.clear_grid()
        self.original_bits = []

        try:
            ctype = self.main.controller.detect_card_type()
        except Exception:
            ctype = None

        if not hasattr(card, "read_protection_memory"):
            self.lbl_info.setText(tr("msg.no_protection_memory"))
            self.btn_apply.setEnabled(False)
            return

        try:
            card.read_protection_memory()
        except Exception as exc:
            self.lbl_info.setText(str(exc))
            self.btn_apply.setEnabled(False)
            return

        bits = getattr(card, "protection_bits", None)

        if isinstance(bits, dict):
            if bits:
                max_index = max(bits.keys()) + 1
                tmp = [False] * max_index
                for i, v in bits.items():
                    if 0 <= i < max_index:
                        tmp[i] = bool(v)
                bits = tmp
            else:
                bits = []

        if bits is None:
            bits = []

        bits = list(bits)
        self.original_bits = list(bits)
        total = len(bits)

        if total == 0:
            self.lbl_info.setText(tr("msg.no_protection_bits"))
            self.btn_apply.setEnabled(False)
            return

        if ctype in ("SLE4442", "SLE5542"):
            self.btn_apply.setEnabled(True)
        else:
            self.btn_apply.setEnabled(False)

        self.lbl_info.setText(f"{tr('label.protection_bits')}: {total}")

        cols = 16

       
        for c in range(cols):
            lbl = QLabel(f"{c:02X}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-weight:bold; padding:2px;")
            self.grid.addWidget(lbl, 0, c + 1)

   
        for i, prot in enumerate(bits):
            row = i // cols
            col = i % cols

            if col == 0:
                base = row * cols
                off = QLabel(f"{base:04X}")
                off.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                off.setStyleSheet("font-weight:bold; padding-right:6px;")
                self.grid.addWidget(off, row + 1, 0)

            cb = QCheckBox(f"{i:02X}")
            cb.setToolTip(f"{tr('label.bit')} {i:04X}")
            cb.setChecked(prot)

            cb.setEnabled((not prot) and self.btn_apply.isEnabled())

            cb.setProperty("prot_index", i)
            cb.setMinimumWidth(46)
            cb.setMinimumHeight(24)

            cb.stateChanged.connect(lambda s, idx=i: self._on_checkbox_changed(idx))

            self.grid.addWidget(cb, row + 1, col + 1)
            self.checks.append(cb)
            self._update_checkbox_style(i)

    def _on_checkbox_changed(self, idx):
        if 0 <= idx < len(self.checks):
            self._update_checkbox_style(idx)

    def _update_checkbox_style(self, idx):
        cb = self.checks[idx]
        orig = bool(self.original_bits[idx])
        curr = cb.isChecked()

        if orig:
            cb.setStyleSheet("color:#ff4d4d; font-weight:bold;")
        else:
            if curr:
                cb.setStyleSheet("color:#ffa640; font-weight:bold;")
            else:
                cb.setStyleSheet("color:#7dff7d; font-weight:bold;")

    def reload(self):
        if self.card:
            self.load_from_card(self.card)

    def apply_changes(self):
        if not self.card or not hasattr(self.card, "set_protection_bits"):
            return

        if hasattr(self.card, "ensure_authenticated"):
            ok = self.card.ensure_authenticated(self.main)
            if not ok:
                QMessageBox.critical(self, tr("msg.error"), tr("msg.psc_required"))
                return
        else:
            try:
                sm = self.card.read_security_memory()
                if sm[0] == 0:
                    QMessageBox.critical(self, tr("msg.error"), tr("msg.psc_required"))
                    return
            except Exception as e:
                QMessageBox.critical(self, tr("msg.error"), str(e))
                return

        targets = []
        for i, cb in enumerate(self.checks):
            curr = cb.isChecked()
            orig = bool(self.original_bits[i])
            if curr and not orig:
                targets.append(i)

        if not targets:
            QMessageBox.information(self, tr("msg.information"), tr("msg.no_protection_changes"))
            return

        reply = QMessageBox.question(
            self,
            tr("msg.confirm_protection"),
            tr("msg.confirm_protection_text"),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            self.card.set_protection_bits(targets)
            self.main.log(tr("log.protection_written_ok"))
            self.load_from_card(self.card)
        except Exception as exc:
            QMessageBox.critical(self, tr("msg.error"), str(exc))
            self.main.log(f"{tr('log.error_writing_protection')}: {exc}")
