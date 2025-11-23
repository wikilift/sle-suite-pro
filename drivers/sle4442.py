                    
                                                             
                                                                                   

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
      
        self.protection_bits = {}
        idx = 0
        for byte in pm:
            mask = 1
            for _ in range(8):
                free = (byte & mask) != 0
                                                
                self.protection_bits[idx] = not free
                mask <<= 1
                idx += 1

        self._log(tr("log.pm_decoded"))              

    def protect_byte(self, addr: int):
       
        super().protect_byte(addr)
        if addr in self.protection_bits:
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

        self._log(f"{tr('msg.page_write')} en {addr}…")
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

        H1 = self.main_memory[0]
        H2 = self.main_memory[1]
        H3 = self.main_memory[2]
        H4 = self.main_memory[3]

                                        
                    
                                        
        proto_type = (H1 >> 4) & 0x0F
        proto_desc = self._protocol_desc(proto_type)
        self.atr_header.append(
            ChipData("B0-H1", "Protocol Type", f"{proto_type}", proto_desc)
        )

        structure = H1 & 0x07
        self.atr_header.append(
            ChipData("B0-H1", "Structure", f"{structure:02X}", self._structure_desc(structure))
        )

                       
        read_mode = (H2 >> 7) & 0x01
        self.atr_header.append(
            ChipData(
                "B1-H2",
                "Read Mode",
                f"{read_mode}",
                tr("desc.read_to_end") if read_mode == 0 else tr("desc.read_with_len"),
            )
        )

                                  
        data_units = (H2 >> 3) & 0x0F
        units_desc = self._data_units_desc(data_units)
        self.atr_header.append(
            ChipData("B1-H2", "Number of data units", f"{data_units:02X}", units_desc)
        )

                                 
        unit_len = H2 & 0x07
        self.atr_header.append(
            ChipData("B1-H2", "Length of data unit", f"{unit_len:02X}", f"{2**unit_len} {tr('desc.bits')}")
        )

                      
        self.atr_header.append(
            ChipData("B2-H3", "Category", f"{H3:02X}", "")
        )

                                
        dir_ref = H4 & 0x7F
        self.atr_header.append(
            ChipData("B3-H4", "DIR Data Ref", f"{dir_ref}", "")
        )

                                        
                  
                                        
        self.atr_data.append(
            ChipData("B4-TM", "Manuf Tag", f"{self.main_memory[4]:02X}", "")
        )
        self.atr_data.append(
            ChipData("B5-LM", "Length of Manuf data", f"{self.main_memory[5]:02X}", "")
        )
        self.atr_data.append(
            ChipData("B6-ICM", "IC Manuf ID", f"{self.main_memory[6]:02X}", "")
        )
        self.atr_data.append(
            ChipData("B7-ICT", "IC Type", f"{self.main_memory[7]:02X}", "")
        )

        fab = self._hex(self.main_memory[8:13])
        self.atr_data.append(
            ChipData("B8/B12-ICCF", "IC Fabr ID", fab, "")
        )

        sn = self._hex(self.main_memory[13:17])
        self.atr_data.append(
            ChipData("B13/B16-ICCSN", "IC Serial No", sn, "")
        )

                                        
                  
                                        
        self.dir_data.append(
            ChipData("B17-TT", "App Data Tag", f"{self.main_memory[17]:02X}", "")
        )
        self.dir_data.append(
            ChipData("B18-LT", "Len of app Template", f"{self.main_memory[18]}", "")
        )
        self.dir_data.append(
            ChipData("B19-TA", "Tag of AID", f"{self.main_memory[19]:02X}", "")
        )
        self.dir_data.append(
            ChipData("B20-LA", "Len of AID", f"{self.main_memory[20]}", "")
        )

        aid = self._hex(self.main_memory[21:27])
        self.dir_data.append(
            ChipData("B21/B26-AID", "AID", aid, "")
        )

        self.dir_data.append(
            ChipData("B27-TD", "Discretionary Tag", f"{self.main_memory[27]:02X}", "")
        )
        self.dir_data.append(
            ChipData("B28-LD", "Discretionary Len", f"{self.main_memory[28]}", "")
        )
        self.dir_data.append(
            ChipData("B29-AP", "App Per Id", f"{self.main_memory[29]:02X}", "")
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
            1: "128",
            2: "256",
            3: "512",
            4: "1024",
            5: "2048",
            6: "4096",
            15: tr("desc.rfu"),
        }
        return table.get(n, tr("desc.greater_4096"))