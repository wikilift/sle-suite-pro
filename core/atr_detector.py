from core.language_manager import tr              

class CardType:
    SLE4442 = "SLE4442"
    SLE4428 = "SLE4428"
    SLE5542 = "SLE5542"
    SLE5528 = "SLE5528"
    UNKNOWN = "UNKNOWN"


class ATRDetector:

    @staticmethod
    def detect(atr, conn=None, logger=None):

        if logger:
            logger(tr("log.atr_received") + ": " + " ".join(f"{b:02X}" for b in atr))


        if atr[:4] == [0x3B, 0x04, 0xA2, 0x13]:
            if logger: logger(tr("msg.detected_4442"))
            return CardType.SLE4442

        if atr[:4] == [0x3B, 0x04, 0x92, 0x23]:
            if logger: logger("Detectado por ATR → SLE4428")
            return CardType.SLE4428

     
        if len(atr) >= 6:
            hist = atr[-5:]
          
            if hist[0] == 0xA2:
                return CardType.SLE5542
            if hist[0] == 0x28:
                return CardType.SLE5528

        if logger:
            logger(tr("msg.atr_unknown"))
        return CardType.UNKNOWN
