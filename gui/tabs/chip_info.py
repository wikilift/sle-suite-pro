from types import SimpleNamespace

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt
from core.language_manager import tr


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
        self.grp_sm = self._make_group(tr("group.security_memory"))

        for g in (
            self.grp_atr,
            self.grp_chip,
            self.grp_manuf,
            self.grp_ic,
            self.grp_dir,
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
            self.grp_ic, self.grp_dir, self.grp_sm
        ):
            while group.grid.count():
                item = group.grid.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()

    def _decode_common_layout(self, mem_bytes):
        header = []
        manuf = []
        app = []

        if len(mem_bytes) < 4:
            return header, manuf, app

        b0 = mem_bytes[0]
        b1 = mem_bytes[1]
        b2 = mem_bytes[2]
        b3 = mem_bytes[3]

        proto = (b0 >> 4) & 0x0F
        struct = b0 & 0x0F

        proto_map = {
            8: tr("desc.protocol_serial"),
            9: tr("desc.protocol_3wire"),
            10: tr("desc.protocol_2wire"),
        }
        proto_desc = proto_map.get(proto, f"{tr('desc.unknown')} ({proto:X})")

        struct_map = {
            2: tr("desc.structure_general"),
        }
        struct_desc = struct_map.get(struct, f"{tr('desc.unknown')} ({struct:X})")

        header.append(SimpleNamespace(
            name=tr("label.b0_h1_protocol_type"),
            value=f"{proto:X} – {proto_desc}"
        ))
        header.append(SimpleNamespace(
            name=tr("label.b0_h2_structure"),
            value=f"{struct:02X} – {struct_desc}"
        ))

        read_mode = (b1 >> 7) & 0x01
        data_units = (b1 >> 3) & 0x0F
        unit_len = b1 & 0x07

        read_desc = tr("desc.read_to_end") if read_mode == 0 else tr("desc.read_with_len")

        units_map = {
            0: tr("desc.no_indication"),
            1: tr("desc.128"),
            2: tr("desc.256"),
            3: tr("desc.512"),
            4: tr("desc.1024"),
            5: tr("desc.2048"),
            6: tr("desc.4096"),
            15: tr("desc.rfu"),
        }
        units_desc = units_map.get(data_units, tr("desc.greater_4096"))

        header.append(SimpleNamespace(
            name=tr("label.b1_read_mode"),
            value=f"{read_mode} – {read_desc}"
        ))
        header.append(SimpleNamespace(
            name=tr("label.b1_num_data_units"),
            value=f"{data_units:02X} – {units_desc}"
        ))
        header.append(SimpleNamespace(
            name=tr("label.b1_len_data_unit"),
            value=f"{unit_len:02X} – {1 << unit_len} {tr('desc.bits')}"
        ))

        header.append(SimpleNamespace(
            name=tr("label.b2_category"),
            value=f"{b2:02X}"
        ))

        dir_ref = b3 & 0x7F
        header.append(SimpleNamespace(
            name=tr("label.b3_dir_data_ref"),
            value=f"{dir_ref:02X}"
        ))

        if len(mem_bytes) >= 17:
            manuf.append(SimpleNamespace(name=tr("label.b4_manuf_tag"), value=f"{mem_bytes[4]:02X}"))
            manuf.append(SimpleNamespace(name=tr("label.b5_len_manuf_data"), value=f"{mem_bytes[5]:02X}"))
            manuf.append(SimpleNamespace(name=tr("label.b6_ic_manuf_id"), value=f"{mem_bytes[6]:02X}"))
            manuf.append(SimpleNamespace(name=tr("label.b7_ic_type"), value=f"{mem_bytes[7]:02X}"))

            ic_fabr = mem_bytes[8:13]
            ic_fabr_hex = "-".join(f"{b:02X}" for b in ic_fabr)
            manuf.append(SimpleNamespace(name=tr("label.b8_b12_ic_fabr_id"), value=ic_fabr_hex))

            ic_sn = mem_bytes[13:17]
            ic_sn_hex = "-".join(f"{b:02X}" for b in ic_sn)
            manuf.append(SimpleNamespace(name=tr("label.b13_b16_ic_serial_no"), value=ic_sn_hex))

        if len(mem_bytes) >= 30:
            app.append(SimpleNamespace(name=tr("label.b17_app_data_tag"), value=f"{mem_bytes[17]:02X}"))
            app.append(SimpleNamespace(name=tr("label.b18_len_app_template"), value=f"{mem_bytes[18]:02X}"))
            app.append(SimpleNamespace(name=tr("label.b19_tag_of_aid"), value=f"{mem_bytes[19]:02X}"))
            app.append(SimpleNamespace(name=tr("label.b20_len_of_aid"), value=f"{mem_bytes[20]:02X}"))

            aid = mem_bytes[21:27]
            aid_hex = "-".join(f"{b:02X}" for b in aid)
            app.append(SimpleNamespace(name=tr("label.b21_b26_aid"), value=aid_hex))

            app.append(SimpleNamespace(name=tr("label.b27_discretionary_tag"), value=f"{mem_bytes[27]:02X}"))
            app.append(SimpleNamespace(name=tr("label.b28_discretionary_len"), value=f"{mem_bytes[28]:02X}"))
            app.append(SimpleNamespace(name=tr("label.b29_app_per_id"), value=f"{mem_bytes[29]:02X}"))

        return header, manuf, app

    def _build_sm_4428(self, card):
        try:
            sm = card.read_security_memory()
        except Exception as e:
            self._add_line(self.grp_sm, 0, tr("msg.error"), str(e))
            return

        sm_hex = " ".join(f"{b:02X}" for b in sm)
        self._add_line(self.grp_sm, 0, tr("label.raw"), sm_hex)

        ec = sm[0] if len(sm) > 0 else 0
        attempts = 3 if ec == 0x7F else (ec & 0x0F)

        if attempts >= 3:
            col = "#7dff7d"
        elif attempts == 2:
            col = "#ffdd7d"
        elif attempts == 1:
            col = "#ffb84d"
        else:
            col = "#ff4d4d"

        lbl = QLabel(str(attempts))
        lbl.setStyleSheet(f"padding:4px; font-weight:bold; background:{col};")
        self.grp_sm.grid.addWidget(QLabel(tr("label.chv1") + tr("label.attempts_left")), 1, 0)
        self.grp_sm.grid.addWidget(lbl, 1, 1)

        if len(sm) >= 3:
            psc = sm[1:3]
            psc_hex = " ".join(f"{b:02X}" for b in psc)
            psc_lbl = QLabel(psc_hex)
            if all(x == 0xFF for x in psc):
                psc_lbl.setStyleSheet("background:#ffdd7d; padding:4px;")
            self.grp_sm.grid.addWidget(QLabel(tr("label.psc_mem")), 2, 0)
            self.grp_sm.grid.addWidget(psc_lbl, 2, 1)

    def _build_sm_4442(self, card):
        try:
            sm = card.read_security_memory()
        except Exception as e:
            self._add_line(self.grp_sm, 0, tr("msg.error"), str(e))
            return

        sm_hex = " ".join(f"{b:02X}" for b in sm)
        self._add_line(self.grp_sm, 0, tr("label.raw"), sm_hex)

        counter = card.error_counter if hasattr(card, "error_counter") else (sm[0] if sm else 0)

        if counter >= 3:
            col = "#7dff7d"
        elif counter == 2:
            col = "#ffdd7d"
        elif counter == 1:
            col = "#ffb84d"
        else:
            col = "#ff4d4d"

        lbl = QLabel(str(counter))
        lbl.setStyleSheet(f"padding:4px; font-weight:bold; background:{col};")
        self.grp_sm.grid.addWidget(QLabel(tr("label.attempts_left")), 1, 0)
        self.grp_sm.grid.addWidget(lbl, 1, 1)

        if len(sm) > 1:
            psc = sm[1:4]
            psc_hex = " ".join(f"{b:02X}" for b in psc)
            psc_lbl = QLabel(psc_hex)
            if all(x == 0xFF for x in psc):
                psc_lbl.setStyleSheet("background:#ffdd7d; padding:4px;")
            self.grp_sm.grid.addWidget(QLabel(tr("label.psc_mem")), 2, 0)
            self.grp_sm.grid.addWidget(psc_lbl, 2, 1)

    def load_chip(self, card):
        self.clear()

        atr = self.main.controller.conn.getATR()
        atr_hex = " ".join(f"{b:02X}" for b in atr)
        self._add_line(self.grp_atr, 0, tr("label.atr"), atr_hex)

        ctype = getattr(self.main.controller, "card_type", None)
        if not ctype:
            ctype = self.main.controller.detect_card_type()
        self._add_line(self.grp_chip, 0, tr("label.detected_type"), ctype)

        mem = getattr(card, "main_memory", None)
        if not mem:
            try:
                mem = card.read_all()
            except Exception as e:
                self.main.log(f"{tr('log.memory_read_fail')}: {e}")
                mem = []

        mem_bytes = list(mem) if mem else []
        header_items, manuf_items, dir_items = self._decode_common_layout(mem_bytes)

        r = 1
        for it in header_items:
            self._add_line(self.grp_chip, r, it.name + ":", it.value)
            r += 1

        r = 0
        for it in manuf_items:
            if tr("label.ic_fabr_id_lookup") in it.name or tr("label.ic_serial_no_lookup") in it.name:
                self._add_line(self.grp_ic, r, it.name + ":", it.value)
            else:
                self._add_line(self.grp_manuf, r, it.name + ":", it.value)
            r += 1

        r = 0
        for it in dir_items:
            self._add_line(self.grp_dir, r, it.name + ":", it.value)
            r += 1

        for group in (self.grp_sm,):
            while group.grid.count():
                item = group.grid.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()

        if ctype in ("SLE4428", "SLE5528"):
            self._build_sm_4428(card)
        else:
            self._build_sm_4442(card)