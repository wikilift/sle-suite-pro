                      

class CardType:
    SLE4442 = "SLE4442"
    SLE5542 = "SLE5542"
    SLE4428 = "SLE4428"
    SLE5528 = "SLE5528"
    UNKNOWN = "UNKNOWN"


class ATRDetector:
 

                                  
    ATR_FAMILY_4442 = [
        [0x3B, 0x65, 0x00, 0x00],
        [0x3B, 0x05, 0xA2],
        [0x3B, 0x04, 0xA2],
        [0x3B, 0x25, 0x00, 0x00],
    ]

    ATR_FAMILY_4428 = [
        [0x3B, 0xE6, 0x00, 0x00],
        [0x3B, 0x05, 0x28],
        [0x3B, 0x04, 0x28],
        [0x3B, 0x46, 0x28],
    ]

    @staticmethod
    def _starts_with(arr, prefix):
        if len(arr) < len(prefix):
            return False
        return arr[:len(prefix)] == prefix

                                                                    
    @classmethod
    def detect_from_atr(cls, atr):
       
        if not atr:
            return CardType.UNKNOWN

        atr = [int(x) for x in atr]

                                    
        for sig in cls.ATR_FAMILY_4442:
            if cls._starts_with(atr, sig):
                return CardType.SLE4442

                                    
        for sig in cls.ATR_FAMILY_4428:
            if cls._starts_with(atr, sig):
                return CardType.SLE4428

                                                
        if len(atr) >= 6:
            hist = atr[-5:]
            if hist[0] == 0xA2:
                return CardType.SLE4442
            if hist[0] == 0x28:
                return CardType.SLE4428

        return CardType.UNKNOWN

                                                                    
    @staticmethod
    def _probe_2wire(conn):
       
        apdu = [0xFF, 0x20, 0x00, 0x00, 0x03, 0xFF, 0xFF, 0xFF]
        _, sw1, _ = conn.transmit(apdu)
        return sw1 in (0x90, 0x63, 0x69)

    @staticmethod
    def _probe_3wire(conn):
    
        apdu = [
            0xFF, 0x70, 0x07, 0x6B, 0x07,
            0xA6, 0x05, 0xA1, 0x03,
            0x0E, 0x00, 0x00, 0x00              
        ]
        _, sw1, _ = conn.transmit(apdu)
        return sw1 in (0x90, 0x63, 0x6A)

                                                                    
    @classmethod
    def detect(cls, atr, conn, logger=None):
  
        if logger:
            logger(f"ATR recibido: {' '.join(f'{b:02X}' for b in atr)}")

                                
        ctype = cls.detect_from_atr(atr)
        if ctype != CardType.UNKNOWN:
            if logger: logger(f"Detectado por ATR → {ctype}")
            return ctype

                                             
        if logger: logger("ATR ambiguo, iniciando probing...")

        is_2w = cls._probe_2wire(conn)
        is_3w = cls._probe_3wire(conn)

        if is_2w and not is_3w:
            if logger: logger("Probado → 2-WIRE (4442/5542)")
            return CardType.SLE4442

        if is_3w and not is_2w:
            if logger: logger("Probado → 3-WIRE (4428/5528)")
            return CardType.SLE4428

                                          
        if is_2w and is_3w:
            if logger: logger("Probado → híbrido → família 55xx")
                            
                                                           
                                                        
            test_3byte = [0xFF, 0x20, 0x00, 0x00, 0x03, 0, 0, 0]
            _, sw1a, _ = conn.transmit(test_3byte)

            if sw1a in (0x90, 0x63, 0x69):
                return CardType.SLE5542
            else:
                return CardType.SLE5528

        return CardType.UNKNOWN
