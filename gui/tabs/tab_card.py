from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox
)
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtCore import QRegularExpression

from gui.widgets.hex_editor import HexEditor


class TabCard(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        layout = QVBoxLayout()
        self.setLayout(layout)

        top = QHBoxLayout()

        self.lbl_psc = QLabel(self.tr("label.psc"))
        top.addWidget(self.lbl_psc)

        self.psc = QLineEdit()
        self.psc.setPlaceholderText(self.tr("placeholder.psc"))
        self.psc.setFixedWidth(120)

        regex = QRegularExpression(r"[0-9A-Fa-f ]+")
        validator = QRegularExpressionValidator(regex, self)
        self.psc.setValidator(validator)
        self.psc.setMaxLength(12)

        top.addWidget(self.psc)

        self.btn_auth = QPushButton(self.tr("btn.auth_psc"))
        self.btn_auth.clicked.connect(self.authenticate)
        top.addWidget(self.btn_auth)

        self.btn_change_psc = QPushButton(self.tr("btn.change_psc"))
        self.btn_change_psc.clicked.connect(self.change_psc)
        top.addWidget(self.btn_change_psc)

        self.btn_write = QPushButton(self.tr("btn.write_changes"))
        self.btn_write.clicked.connect(self.write_changes)
        top.addWidget(self.btn_write)

        self.btn_pinobtain = QPushButton(self.tr("btn.obtain_psc"))
        self.btn_pinobtain.clicked.connect(self.obtain_psc)
        top.addWidget(self.btn_pinobtain)
        top.addStretch()
        layout.addLayout(top)

        self.hex = HexEditor()
        layout.addWidget(self.hex)

        self.update_state(connected=False, card_loaded=False)

    def tr(self, key):
        return self.main.tr(key)

    def update_state(self, connected: bool, card_loaded: bool):
        visible = connected and card_loaded

        self.lbl_psc.setVisible(visible)
        self.psc.setVisible(visible)
        self.btn_auth.setVisible(visible)
        self.btn_change_psc.setVisible(visible)
        self.btn_write.setVisible(visible)
        self.btn_pinobtain.setVisible(visible)

    def load_data(self, data: bytes):
        self.adjust_psc_field()
        self.hex.load_data(data)
        self.update_state(connected=True, card_loaded=True)

    def _validate_and_get_psc(self):
        card = self.main.controller.card
        if not card:
            self.main.log(self.tr("msg.no_card_loaded"))
            return None

        name = card.__class__.__name__
        is_3byte = name in ("SLE4442", "SLE5542")
        required_bytes = 3 if is_3byte else 2
        required_hex_chars = required_bytes * 2
        default_hex = "FF FF FF" if is_3byte else "FF FF"

        raw = self.psc.text().strip()
        txt = raw.replace(" ", "").upper()

        if len(txt) != required_hex_chars:
            QMessageBox.warning(
                self, 
                self.tr("msg.warning"), 
                self.tr("msg.psc_invalid_format")
            )
            self.psc.setText(default_hex)
            return None

        try:
            psc_bytes = [int(txt[i : i + 2], 16) for i in range(0, len(txt), 2)]
        except ValueError:
            QMessageBox.warning(
                self, 
                self.tr("msg.warning"), 
                self.tr("msg.psc_invalid_format")
            )
            self.psc.setText(default_hex)
            return None

        normalized = " ".join(f"{b:02X}" for b in psc_bytes)
        self.psc.blockSignals(True)
        self.psc.setText(normalized)
        self.psc.blockSignals(False)

        return psc_bytes

    def authenticate(self):
        psc_bytes = self._validate_and_get_psc()
        if psc_bytes is None:
            return

        try:
            card = self.main.controller.card
            card.authenticate(psc_bytes)
            self.main.log(self.tr("msg.psc_ok"))
            self.main.update_psc_state()

        except Exception as e:
            self.main.log(f"{self.tr('msg.error_auth')} {e}")

    def change_psc(self):
        new_psc = self._validate_and_get_psc()
        if new_psc is None:
            return

        try:
            card = self.main.controller.card
            card.change_psc(new_psc)
            self.main.log(self.tr("msg.psc_changed_ok"))

        except Exception as e:
            self.main.log(f"{self.tr('msg.error_change_psc')} {e}")

    def write_changes(self):
        try:
            card = self.main.controller.card
            if not card:
                self.main.log(self.tr("msg.no_card_loaded"))
                return

            data = self.hex.get_bytes()
            card.write_bytes(0, data)
            self.main.log(self.tr("msg.write_ok"))

        except Exception as e:
            self.main.log(f"{self.tr('msg.error_write')} {e}")

    def adjust_psc_field(self):
        card = self.main.controller.card
        if not card:
            return

        name = card.__class__.__name__

        if name in ("SLE4442", "SLE5542"):
            self.psc.setMaxLength(12)
            self.psc.setPlaceholderText(self.tr("placeholder.psc_3byte"))
            self.lbl_psc.setText(self.tr("label.psc_3bytes"))
        else:
            self.psc.setMaxLength(8)
            self.psc.setPlaceholderText(self.tr("placeholder.psc_2byte"))
            self.lbl_psc.setText(self.tr("label.psc_2bytes"))

    def obtain_psc(self):
        try:
            card = self.main.controller.card
            if not card:
                self.main.log(self.tr("msg.no_card_loaded"))
                return

            psc = self.main.controller.obtain_psc()
            if psc is None:
                self.main.log(self.tr("msg.psc_recovery_not_supported"))
                return

            hex_psc = " ".join(f"{b:02X}" for b in psc)

            self.psc.blockSignals(True)
            self.psc.setText(hex_psc)
            self.psc.blockSignals(False)

            self.main.log(f"{self.tr('msg.psc_found')}: {hex_psc} ")

        except Exception as e:
            self.main.log(f"{self.tr('msg.error_psc')} {e}")