                      

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel,
    QLineEdit, QRadioButton, QButtonGroup
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
        self.psc.setMaxLength(8)                         

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

                                       
                            
                                       
        self.btn_hex = QRadioButton(self.tr("view.hex"))
        self.btn_ascii = QRadioButton(self.tr("view.ascii"))

                     
        self.btn_hex.setChecked(True)

        group = QButtonGroup(self)
        group.setExclusive(True)
        group.addButton(self.btn_hex)
        group.addButton(self.btn_ascii)

        self.btn_hex.toggled.connect(self.update_view_mode)
        self.btn_ascii.toggled.connect(self.update_view_mode)

        top.addWidget(self.btn_hex)
        top.addWidget(self.btn_ascii)

        top.addStretch()
        layout.addLayout(top)

                                       
                    
                                       
        self.hex = HexEditor()
        layout.addWidget(self.hex)

                       
        self.update_state(connected=False, card_loaded=False)

                                                           
                   
                                                           
    def tr(self, key):
        return self.main.tr(key)

                                                           
                                  
                                                           
    def update_view_mode(self):
        if self.btn_hex.isChecked():
            self.hex.set_view_ascii(False)
        else:
            self.hex.set_view_ascii(True)

                                                           
               
                                                           
    def update_state(self, connected: bool, card_loaded: bool):
        visible = connected and card_loaded

        self.lbl_psc.setVisible(visible)
        self.psc.setVisible(visible)
        self.btn_auth.setVisible(visible)
        self.btn_change_psc.setVisible(visible)
        self.btn_write.setVisible(visible)
        self.btn_pinobtain.setVisible(visible)
        self.btn_hex.setVisible(visible)
        self.btn_ascii.setVisible(visible)

                                                           
                    
                                                           
    def load_data(self, data: bytes):
        self.hex.load_data(data)
        self.update_state(connected=True, card_loaded=True)

                                                           
                             
                                                           
    def _parse_psc_from_edit(self):
        raw = self.psc.text().strip()
        txt = raw.replace(" ", "").upper()

                                                        
        if len(txt) not in (4, 6):
            self.main.log(self.tr("msg.psc_invalid"))
            return None

        try:
            psc_bytes = [int(txt[i:i + 2], 16) for i in range(0, len(txt), 2)]
        except ValueError:
            self.main.log(self.tr("msg.psc_invalid"))
            return None

                                        
        normalized = " ".join(f"{b:02X}" for b in psc_bytes)
        self.psc.blockSignals(True)
        self.psc.setText(normalized)
        self.psc.blockSignals(False)

        return psc_bytes


                                                           
                      
                                                           
    def authenticate(self):
        psc_bytes = self._parse_psc_from_edit()
        if psc_bytes is None:
            return

        try:
            card = self.main.controller.card
            if not card:
                self.main.log(self.tr("msg.no_card_loaded"))
                return

            card.authenticate(psc_bytes)
            self.main.log(self.tr("msg.psc_ok"))

        except Exception as e:
            self.main.log(f"{self.tr('msg.error_auth')} {e}")

                                                           
                
                                                           
    def change_psc(self):
     
        new_psc = self._parse_psc_from_edit()
        if new_psc is None:
            return

        try:
            card = self.main.controller.card
            if not card:
                self.main.log(self.tr("msg.no_card_loaded"))
                return

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

                                                           
                                    
                                                           
                                                               
                                    
                                                           
    def obtain_psc(self):
        try:
            card = self.main.controller.card
            if not card:
                self.main.log(self.tr("msg.no_card_loaded"))
                return

                                                        
            psc = self.main.controller.obtain_psc()
            hex_psc = " ".join(f"{b:02X}" for b in psc)

                                        
            self.psc.blockSignals(True)
            self.psc.setText(hex_psc)
            self.psc.blockSignals(False)

                                             
            self.main.log(f"{self.tr('msg.psc_found')}: {hex_psc} "
                          f"({self.tr('msg.psc_not_auto_auth')})")


        except Exception as e:
            self.main.log(f"{self.tr('msg.error_psc')} {e}")


