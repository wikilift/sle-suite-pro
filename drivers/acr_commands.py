
class ACS:
    READ_BINARY = 0xB0
    READ_PROTECTION = 0xB1
    READ_SEC_MEMORY = 0x31
    VERIFY_PSC = 0x20

    WRITE_BINARY = 0xD0
    WRITE_PROTECTION = 0x30
    SELECT_CARD = 0xA4


class SLE3W:
  

    READ_9BITS_DATA_WITH_PROTECT = 0x0C
    READ_8BITS_DATA_NO_PROTECT = 0x0E
    WRITE_AND_ERASE_WITH_PROTECT = 0x31
    WRITE_AND_ERASE_NO_PROTECT = 0x33
    WRITE_ERROR_COUNTER = 0xF2
    VERIFY_PSC = 0xCD
    COMPARE_AND_PROTECT = 0x30


class HID:
    READ_MEMORY = 0xB0
    WRITE_MEMORY = 0xD6
    READ_PROTECTION = 0x3A
    COMPARE_AND_PROTECT = 0x30
    VERIFY = 0x20
    CHANGE_PSC = 0x21


class FIXED:
    ERROR_COUNTER = 1021
    PSC1 = 1022
    PSC2 = 1023
    PSC_EC_AREA = 1008


                                                               
                    
                                                               

def build_read(addr: int, length: int):
    return [0xFF, ACS.READ_BINARY, 0x00, addr & 0xFF, length]


def build_read_protection_4442():
    return [0xFF, ACS.READ_PROTECTION, 0x00, 0x00, 0x04]


def build_read_security_memory():
    return [0xFF, ACS.READ_SEC_MEMORY, 0x00, 0x00, 0x04]


def build_authenticate(psc):
    return [0xFF, ACS.VERIFY_PSC, 0x00, 0x00, 0x03] + list(psc)


def build_write(addr: int, data):
    ln = len(data)
    return [0xFF, ACS.WRITE_BINARY, 0x00, addr & 0xFF, ln] + list(data)


def build_protect_byte(addr: int):
    return [0xFF, ACS.WRITE_PROTECTION, 0x00, addr & 0xFF, 0x01, 0xFF]


                                                               
                          
                                                               

def build_3w_command(cmd: int, addr: int, data: int = 0):

    base = [
        0xFF,                     
        0x70,                        
        0x07,      
        0x6B,      
        0x07,      
        0xA6,
        0x05,
        0xA1,
        0x03,
        0x00,       
        0x00,        
        0x00,        
        0x00,           
    ]

    base[9] = cmd & 0xFF
    base[10] = addr & 0xFF
    base[11] = data & 0xFF
    return base


def build_3w_read8(addr):
    return build_3w_command(SLE3W.READ_8BITS_DATA_NO_PROTECT, addr)


def build_3w_read9(addr):
    return build_3w_command(SLE3W.READ_9BITS_DATA_WITH_PROTECT, addr)


def build_3w_write(addr, value, protect=True):
    cmd = (
        SLE3W.WRITE_AND_ERASE_WITH_PROTECT
        if protect
        else SLE3W.WRITE_AND_ERASE_NO_PROTECT
    )
    return build_3w_command(cmd, addr, value)


def build_3w_verify(psc):
                                                 
    return build_3w_command(SLE3W.VERIFY_PSC, FIXED.PSC1, psc[0])


                                                               
                                                            
                                                               

def build_hid_read(addr: int, length: int):
    return [0xFF, HID.READ_MEMORY, (addr >> 8) & 0xFF, addr & 0xFF, length]


def build_hid_write(addr: int, data):
    ln = len(data)
    return [0xFF, HID.WRITE_MEMORY, (addr >> 8) & 0xFF, addr & 0xFF, ln] + list(data)


def build_hid_read_protection(addr: int, length: int):
    return [
        0xFF,
        HID.READ_PROTECTION,
        (addr >> 8) & 0xFF,
        addr & 0xFF,
        length,
    ]


def build_hid_compare_and_protect(addr: int, value: int):
    return [
        0xFF,
        HID.COMPARE_AND_PROTECT,
        (addr >> 8) & 0xFF,
        addr & 0xFF,
        0x01,
        value,
    ]


def build_hid_verify(psc):
    return [0xFF, HID.VERIFY, 0x00, 0x00, 0x02] + list(psc)


def build_hid_change_psc(psc_old, psc_new):
    return [0xFF, HID.CHANGE_PSC, 0x00, 0x00, 0x04] + list(psc_old) + list(psc_new)

