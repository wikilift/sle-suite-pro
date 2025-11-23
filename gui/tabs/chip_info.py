                          

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt
from core.language_manager import tr                      


                                                               
                  
                                                               
def make_square(text, color):
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"""
        background:{color};
        border:1px solid #333;
        font-weight:bold;
        """
    )
    lbl.setFixedSize(26, 26)                       
    return lbl


class TabChipInfo(QWidget):
  
    def __init__(self, main):
        super().__init__()
        self.main = main

                     
        root = QVBoxLayout()
        self.setLayout(root)

                          
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        root.addWidget(scroll)

        container = QWidget()
        self.layout = QVBoxLayout()
        container.setLayout(self.layout)
        scroll.setWidget(container)

                
        self.grp_atr = self._make_group(tr("group.atr"))
        self.grp_chip = self._make_group(tr("group.chip"))
        self.grp_manuf = self._make_group(tr("group.manufacturer"))
        self.grp_ic = self._make_group(tr("group.ic_info"))
        self.grp_dir = self._make_group(tr("group.dir_info"))
        self.grp_pm = self._make_group(tr("group.protection_memory"))
        self.grp_sm = self._make_group(tr("group.security_memory"))

        for g in (
            self.grp_atr,
            self.grp_chip,
            self.grp_manuf,
            self.grp_ic,
            self.grp_dir,
            self.grp_pm,                
            self.grp_sm,
        ):
            self.layout.addWidget(g)

        self.layout.addStretch()

                                                                   
    def _make_group(self, title):
        box = QGroupBox(title)
        layout = QGridLayout()
        layout.setColumnStretch(1, 1)
        box.setLayout(layout)
        box.grid = layout
        return box

    def _add_line(self, box, row, name, value):
        lbl = QLabel(name)
        lbl.setStyleSheet("font-weight:bold;")
        box.grid.addWidget(lbl, row, 0)
        box.grid.addWidget(QLabel(value), row, 1)

                                                                   
    def clear(self):
        for group in (
            self.grp_atr, self.grp_chip, self.grp_manuf,
            self.grp_ic, self.grp_dir, self.grp_pm, self.grp_sm
        ):
            while group.grid.count():
                item = group.grid.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()

                                                                   
    def load_chip(self, card):
   
        self.clear()

                                                                   
             
                                                                   
        atr = self.main.controller.conn.getATR()
        atr_hex = " ".join(f"{b:02X}" for b in atr)
        self._add_line(self.grp_atr, 0, tr("label.atr"), atr_hex)

                                                                   
                       
                                                                   
        ctype = self.main.controller.detect_card_type()
        self._add_line(self.grp_chip, 0, tr("label.detected_type"), ctype)

                                                                   
                          
                                                                   
        card.generate_chip_data()

        r = 0
        for item in card.atr_header:
            self._add_line(self.grp_chip, r, f"{item.name}:", item.value)
            r += 1

        r = 0
        for item in card.atr_data:
            self._add_line(self.grp_manuf, r, f"{item.name}:", item.value)
            r += 1

        r = 0
        for item in card.dir_data:
            self._add_line(self.grp_dir, r, f"{item.name}:", item.value)
            r += 1

                                                                   
                                                         
                                                                   
        try:
            pm = card.read_protection_memory()
            pm_hex = " ".join(f"{b:02X}" for b in pm)

            self._add_line(self.grp_pm, 0, tr("label.pm_bytes"), pm_hex)

                                   
            self._add_line(self.grp_pm, 1, tr("label.bitfield"), "")

                                        
            row = 2
            col = 0

            for i in range(32):
                prot = card.protection_bits[i]
                color = "#ff4d4d" if prot else "#7dff7d"
                square = make_square("■" if prot else "□", color)

                lbl = QLabel(f"{i:02d}")
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet("font-weight:bold;")
                lbl.setFixedWidth(30)

                self.grp_pm.grid.addWidget(lbl, row, col * 2)
                self.grp_pm.grid.addWidget(square, row, col * 2 + 1)

                col += 1
                if col == 4:                                
                    col = 0
                    row += 1

        except Exception as e:
            self._add_line(self.grp_pm, 0, tr("msg.error"), str(e))

                                                                   
                         
                                                                   
        try:
            sm = card.read_security_memory()
            sm_hex = " ".join(f"{b:02X}" for b in sm)
            attempts = card.error_counter

            self._add_line(self.grp_sm, 0, tr("label.raw"), sm_hex)

                            
            if attempts >= 3:
                col = "#7dff7d"
            elif attempts == 2:
                col = "#ffdd7d"
            elif attempts == 1:
                col = "#ffb84d"
            else:
                col = "#ff4d4d"

            attempts_lbl = QLabel(str(attempts))
            attempts_lbl.setStyleSheet(f"background:{col}; padding:4px; font-weight:bold;")
            self.grp_sm.grid.addWidget(QLabel(tr("label.attempts_left")), 1, 0)
            self.grp_sm.grid.addWidget(attempts_lbl, 1, 1)

                        
            psc = sm[1:]
            psc_hex = " ".join(f"{b:02X}" for b in psc)

            psc_lbl = QLabel(psc_hex)
            if all(x == 0xFF for x in psc):
                psc_lbl.setStyleSheet("background:#ffdd7d; padding:4px; font-weight:bold;")

            self.grp_sm.grid.addWidget(QLabel(tr("label.pin_stored")), 2, 0)
            self.grp_sm.grid.addWidget(psc_lbl, 2, 1)

        except Exception as e:
            self._add_line(self.grp_sm, 0, tr("msg.error"), str(e))