                 
                                            
                                                                      

from core.language_manager import tr                      

class Page16:
    

    def __init__(self, addr_from: int, data: list[int]):
     
        self.addr_from = addr_from
        self.addr_to = addr_from + 15

        if len(data) != 16:
            raise ValueError(tr("error.page_not_16bytes"))              

                                                      
        self.data = list(data)

        self.dirty = False
        self.is_ascii = False                   

                                                                        
                         
                                                                        
    def refresh(self, full_memory, start_addr=None):
   
        addr = self.addr_from if start_addr is None else start_addr
        self.data = list(full_memory[addr:addr+16])
        self.dirty = False

                                                                        
                   
                                                                        
    def set_byte(self, index: int, value: int):
   
        if not (0 <= index < 16):
            raise ValueError(tr("error.index_out_of_range"))

        if not (0 <= value <= 255):
            raise ValueError(tr("error.value_not_byte"))              

        self.data[index] = value
        self.dirty = True

                                                                        
                                  
                                                                        
    def to_hex(self):
        return " ".join(f"{b:02X}" for b in self.data)

    def to_ascii(self):
        chars = []
        for b in self.data:
            chars.append(chr(b) if 32 <= b <= 126 else ".")
        return "".join(chars)

                                                                        
                                                           
                                                                        
    def serialize(self):
        return self.to_hex()

    @staticmethod
    def deserialize(addr, text_line):
     
        parts = text_line.strip().split()
        if len(parts) != 16:
            raise ValueError(tr("error.deserialize_16bytes"))

        data = [int(h, 16) for h in parts]
        return Page16(addr, data)

                                                                        
                           
                                                                        
    def __str__(self):
        mode = tr("view.ascii") if self.is_ascii else tr("view.hex")
                                                                    
                                        
        return f"{tr('label.page')} {self.addr_from}-{self.addr_to} [{mode}] {self.to_hex()}"