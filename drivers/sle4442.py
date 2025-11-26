from .base_card import BaseCard
from model.page16 import Page16
from model.chipdata import ChipData
from core.language_manager import tr                      


class SLE4442(BaseCard):

    def __init__(self, conn, logger=None):
        super().__init__(conn=conn, logger=logger)
        self.size = 256
        self.page_size = 16
        self.main_memory = [0xFF] * self.size
        self.protection_memory = [0xFF] * 4
        self.protection_bits: dict[int, bool] = {i: False for i in range(32)}
        self.security_memory = [0, 0xFF, 0xFF, 0xFF]
        self.pages: list[Page16] = []
        self.atr_header: list[ChipData] = []
        self.atr_data: list[ChipData] = []
        self.dir_data: list[ChipData] = []

    @property
    def error_counter(self) -> int:
        return self.security_memory[0] if self.security_memory else 0

    def _build_pages_from_memory(self):
        self.pages.clear()
        for addr in range(0, self.size, self.page_size):
            chunk = self.main_memory[addr:addr + self.page_size]
            page = Page16(addr, chunk)
            self.pages.append(page)

    def set_display_mode(self, is_ascii: bool):
        for p in self.pages:
            p.is_ascii = is_ascii

    def read_all(self):
        try:
            self._log(tr("log.select_file"))                                           
            self.conn.transmit([0xFF, 0xA4, 0x00, 0x00, 0x01, 0x06])
        except Exception:
            pass

        raw = super().read_all()
        self.main_memory = raw[:]                  
        self._build_pages_from_memory()
        return raw

    def read_page(self, addr_from: int) -> Page16:
        if addr_from % self.page_size != 0:
            raise ValueError(tr("error.addr_not_mult_16"))

        data = self.read_range(addr_from, self.page_size)

        for i, b in enumerate(data):
            self.main_memory[addr_from + i] = b

        for p in self.pages:
            if p.addr_from == addr_from:
                p.data = data[:]
                p.dirty = False
                return p

        page = Page16(addr_from, data)
        self.pages.append(page)
        return page

    def read_bytes(self, addr: int, length: int) -> list[int]:
        data = self.read_range(addr, length)
        for i, b in enumerate(data):
            if addr + i < len(self.main_memory):
                self.main_memory[addr + i] = b
        return data

    def read_protection_memory(self) -> list[int]:
        pm = super().read_protection_memory()
        self._decode_protection_bits(pm)
        return pm

    
    def _decode_protection_bits(self, pm: list[int]):
        
        bits_dict: dict[int, bool] = {}
        idx = 0
        for byte in pm:
            mask = 1
            for _ in range(8):
                free = (byte & mask) != 0   
                bits_dict[idx] = not free   
                mask <<= 1
                idx += 1

        self.protection_bits = bits_dict
        self._log(tr("log.pm_decoded"))
        
    
    @property
    def protection_bits_list(self):
        if isinstance(self.protection_bits, dict):
            out = []
            last = max(self.protection_bits.keys(), default=-1)
            for i in range(last + 1):
                out.append(bool(self.protection_bits.get(i, False)))
            return out
        return list(self.protection_bits)

    def protect_byte(self, addr: int):
        if not self.is_authenticated:
            raise Exception(tr("msg.psc_required"))

        if not (0 <= addr < 32):
            raise ValueError(tr("error.invalid_address"))

        apdu = [0xFF, 0xD1, 0x00, addr & 0xFF, 0x01, 0xFF]
        self.tx(apdu, f"{tr('log.protect_byte')}[{addr}]")

        byte_index = addr // 8
        bit_index = addr % 8
        if 0 <= byte_index < len(self.protection_memory):
            old_val = self.protection_memory[byte_index]
            new_val = old_val & ~(1 << bit_index)
            self.protection_memory[byte_index] = new_val

        if isinstance(self.protection_bits, dict):
            self.protection_bits[addr] = True


    def read_security_memory(self) -> list[int]:
        sm = super().read_security_memory()
        self.security_memory = sm[:]
        return sm
                                        
    def change_psc(self, new_psc: list[int]):
        super().change_psc(new_psc)
                                                                   
    def write_byte(self, addr: int, value: int):
        if not (0 <= value <= 0xFF):
            raise ValueError(tr("error.value_not_byte"))

        self.write_bytes(addr, [value])

        if addr < len(self.main_memory):
            self.main_memory[addr] = value

        page_idx = addr // self.page_size
        offset = addr % self.page_size
        if 0 <= page_idx < len(self.pages):
            self.pages[page_idx].data[offset] = value
            self.pages[page_idx].dirty = False

    def write_page(self, page: Page16):
        addr = page.addr_from
        if addr % self.page_size != 0:
            raise ValueError(tr("error.addr_not_mult_16"))
        if len(page.data) != self.page_size:
            raise ValueError(tr("error.page_not_16bytes"))

        self._log(f"{tr('msg.page_write')} {tr('msg.in')} {addr}…")
        self.write_bytes(addr, page.data)

        for i, b in enumerate(page.data):
            if addr + i < len(self.main_memory):
                self.main_memory[addr + i] = b

        page.dirty = False
        self._log(f"{tr('msg.page_write')} {addr} {tr('msg.write_ok')}")

    def generate_chip_data(self):
        if not self.main_memory or len(self.main_memory) < 30:
            raise Exception(tr("error.memory_empty_read"))

        self.atr_header.clear()
        self.atr_data.clear()
        self.dir_data.clear()

        b0 = self.main_memory[0]
        b1 = self.main_memory[1]
        b2 = self.main_memory[2]
        b3 = self.main_memory[3]

        proto_hi = (b0 >> 4) & 0x0F
        proto_lo = b0 & 0x0F
        length_hi = (b2 >> 4) & 0x0F
        length_lo = b2 & 0x0F

        self.atr_header.append(
            ChipData("B0-H1", tr("label.protocol_type"), f"{proto_hi:X}", tr("desc.protocol_2wire") if proto_hi == 0xA else tr("desc.unknown"))
        )
        self.atr_header.append(
            ChipData("B0-H2", tr("label.structure"), f"{proto_lo:X}", tr("desc.structure_general") if proto_lo == 0x2 else tr("desc.unknown"))
        )

        read_mode = (b1 >> 4) & 0x0F
        num_units = b1 & 0x0F

        self.atr_header.append(
            ChipData("B1-H1", tr("label.read_mode"), f"{read_mode:X}", tr("desc.read_to_end") if read_mode == 0 else tr("desc.unknown"))
        )
        self.atr_header.append(
            ChipData("B1-H2", tr("label.num_data_units"), f"{num_units:X}", tr("desc.256") if num_units == 2 else tr("desc.unknown"))
        )
        self.atr_header.append(
            ChipData("B1-H2", tr("label.len_data_unit"), f"{length_lo:X}", tr("desc.8_bits") if length_lo == 3 else tr("desc.unknown"))
        )

        self.atr_header.append(
            ChipData("B2-H1", tr("label.category"), f"{length_hi:X}", "")
        )
        self.atr_header.append(
            ChipData("B3-H4", tr("label.dir_data_ref"), f"{b3:02X}", "")
        )

        self.atr_data.append(
            ChipData("B4-TM", tr("label.manuf_tag"), f"{self.main_memory[4]:02X}", "")
        )
        self.atr_data.append(
            ChipData("B5-LM", tr("label.len_manuf_data"), f"{self.main_memory[5]:02X}", "")
        )
        self.atr_data.append(
            ChipData("B6-ICM", tr("label.ic_manuf_id"), f"{self.main_memory[6]:02X}", "")
        )
        self.atr_data.append(
            ChipData("B7-ICT", tr("label.ic_type"), f"{self.main_memory[7]:02X}", "")
        )

        fab = "-".join(f"{x:02X}" for x in self.main_memory[8:13])
        self.atr_data.append(
            ChipData("B8-B12", tr("label.ic_fabr_id"), fab, "")
        )

        sn = "-".join(f"{x:02X}" for x in self.main_memory[13:17])
        self.atr_data.append(
            ChipData("B13-B16", tr("label.ic_serial_no"), sn, "")
        )

        self.dir_data.append(
            ChipData("B17-TT", tr("label.app_data_tag"), f"{self.main_memory[17]:02X}", "")
        )
        self.dir_data.append(
            ChipData("B18-LT", tr("label.len_app_template"), f"{self.main_memory[18]}", "")
        )
        self.dir_data.append(
            ChipData("B19-TA", tr("label.tag_of_aid"), f"{self.main_memory[19]:02X}", "")
        )
        self.dir_data.append(
            ChipData("B20-LA", tr("label.len_of_aid"), f"{self.main_memory[20]}", "")
        )

        aid_len = 6
        aid = "-".join(f"{x:02X}" for x in self.main_memory[21:21+aid_len])
        self.dir_data.append(
            ChipData("B21-B26", tr("label.aid"), aid, "")
        )

        self.dir_data.append(
            ChipData("B27-TD", tr("label.discretionary_tag"), f"{self.main_memory[27]:02X}", "")
        )
        self.dir_data.append(
            ChipData("B28-LD", tr("label.discretionary_len"), f"{self.main_memory[28]}", "")
        )
        self.dir_data.append(
            ChipData("B29-AP", tr("label.app_per_id"), f"{self.main_memory[29]:02X}", "")
        )

        self._log(tr("log.chipdata_ok"))
                                      
    def _protocol_desc(self, p: int) -> str:
        if 0 <= p <= 7:
            return tr("desc.reserved_iso")
        if p == 8:
            return tr("desc.protocol_serial")
        if p == 9:
            return tr("desc.protocol_3wire")
        if p == 10:
            return tr("desc.protocol_2wire")
        if p == 15:
            return tr("desc.rfu")
        return tr("desc.not_defined")

    def _structure_desc(self, s: int) -> str:
        if s in (0, 4):
            return tr("desc.reserved_iso")
        if s == 2:
            return tr("desc.structure_general")
        if s == 6:
            return tr("desc.structure_proprietary")
        return tr("desc.special_app")

    def _data_units_desc(self, n: int) -> str:
        table = {
            0: tr("desc.no_indication"),
            1: tr("desc.128"),
            2: tr("desc.256"),
            3: tr("desc.512"),
            4: tr("desc.1024"),
            5: tr("desc.2048"),
            6: tr("desc.4096"),
            15: tr("desc.rfu"),
        }
        return table.get(n, tr("desc.greater_4096"))
    
    
    def set_protection_bits(self, indices: list[int]):
        if not self.is_authenticated:
            raise Exception(tr("msg.psc_required"))

        if not indices:
            return

        for addr in sorted(set(indices)):
            if 0 <= addr < 32:
                if isinstance(self.protection_bits, dict):
                    if self.protection_bits.get(addr, False):
                        continue
                self.protect_byte(addr)

        try:
            pm = super().read_protection_memory()
            self._decode_protection_bits(pm)
        except Exception:
            pass
