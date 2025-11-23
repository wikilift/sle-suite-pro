                    
                                              
                                                
                          

from drivers.base_card import BaseCard
from drivers.acr_commands import (
    build_3w_read8,
    build_3w_read9,
    build_3w_write,
    build_3w_command,
    FIXED
)
from core.language_manager import tr


class SLE4428(BaseCard):
  

    def __init__(self, conn, logger=None):
        super().__init__(conn=conn, logger=logger)

        self.size = 1024
        self.main_memory = bytearray(self.size)
        self.prot = bytearray(self.size)                 
        self.psc = [0xFF, 0xFF]
        self.is_authenticated = False

                                                              
                                 
                                                              
    def _exec_3w(self, label: str, apdu: list, expect_len: int = 0):
      
        self._log(f"<< {label}: {self._hex(apdu)}")

        data = self.tx(apdu, label)

        if expect_len:
            if len(data) < expect_len + 2:
                                            
                error_msg = tr("error.3wbp_format")
                raise Exception(f"{label} {error_msg}")
            return data[2:2 + expect_len]

        return data

                                                              
          
                                                              
    def _read8(self, addr: int):
     
        apdu = build_3w_read8(addr)
        resp = self._exec_3w(f"{tr('log.read_byte_8')}[{addr}]", apdu, expect_len=1)
        return resp[0]

    def _read9(self, addr: int):
      
        apdu = build_3w_read9(addr)
        return self._exec_3w(f"{tr('log.read_byte_9')}[{addr}]", apdu, expect_len=2)

                                               
    def read_all(self):
     
                                                                  
        self._log(f"{tr('log.read_full')} ({self.size} bytes)…")

        for addr in range(self.size):
            data_byte, prot_bit = self._read9(addr)
            self.main_memory[addr] = data_byte
            self.prot[addr] = 1 if prot_bit == 0 else 0
        return bytes(self.main_memory)

    def read_range(self, addr: int, length: int):
        out = bytearray(length)
        for i in range(length):
            data_byte, _ = self._read9(addr + i)
            out[i] = data_byte
        return bytes(out)

                                                              
           
                                                              
    def write_bytes(self, addr: int, data: bytes, protect=False):
        if not self.is_authenticated:
            raise Exception(tr("msg.psc_required"))              

        for i, b in enumerate(data):
            a = addr + i
            if a >= self.size:
                break

            apdu = build_3w_write(a, b, protect)
            self._exec_3w(f"{tr('log.write_byte')}[{a}]", apdu)

            self.main_memory[a] = b
            if protect:
                self.prot[a] = 1

                                                              
                
                                                              
    def protect_byte(self, addr: int):
  
        val = self.main_memory[addr]
        apdu = build_3w_command(0x30, addr, val)
        self._exec_3w(f"{tr('log.protect_byte')}[{addr}]", apdu)
        self.prot[addr] = 1

    def read_protection_map(self):
        return list(self.prot)

                                                              
                        
                                                              
    def authenticate(self, psc):
    
        if len(psc) != 2:
            raise ValueError(tr("error.psc_must_be_2bytes"))

                                                           
        apdu = build_3w_command(0xCD, FIXED.PSC1, psc[0])
        self._exec_3w(tr("log.verify_psc"), apdu)

        self.psc = list(psc)
        self.is_authenticated = True
        self._log(tr("log.auth_ok"))              
        return True