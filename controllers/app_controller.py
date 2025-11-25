from core.language_manager import tr
from drivers.sle4442 import SLE4442
from drivers.sle4428 import SLE4428
from drivers.sle5528 import SLE5528
from drivers.pin_obtain import PinObtain
from core.atr_detector import ATRDetector, CardType

class AppController:
 

    def __init__(self, pcsc, settings, logger):
        self.pcsc = pcsc
        self.settings = settings
        self.log = logger
        self.main = None

        self.conn = None
        self.connected_reader = None
        self.card = None
        self.memory = None
        self.card_type = None

                                                           
                       
                                                           
    def list_readers(self):
        return self.pcsc.list_readers()

    def connect_reader(self, reader):
      
        try:
            conn = reader.createConnection()
            conn.connect()

            self.conn = conn
            self.connected_reader = reader

            atr = conn.getATR()
            return atr

        except Exception as exc:
                                    
            self.conn = None
            self.connected_reader = None
            raise exc

    def disconnect_reader(self):
        if self.conn:
            try:
                self.conn.disconnect()
            except Exception:
                pass

        self.conn = None
        self.connected_reader = None
        self.card = None
        self.memory = None
        self.card_type = None

                                                           
                         
                                                           
    def detect_card_type(self) -> str:
        if self.card_type is not None:
            return self.card_type

        if not self.conn:
            raise Exception(tr("error.no_connection"))

        atr = self.conn.getATR()
        ctype = ATRDetector.detect(atr, self.conn, logger=self.log)

        if ctype == CardType.SLE4442:
            self.card_type = "SLE4442"
        elif ctype == CardType.SLE5542:
            self.card_type = "SLE5542"
        elif ctype == CardType.SLE4428:
            self.card_type = "SLE4428"
        elif ctype == CardType.SLE5528:
            self.card_type = "SLE5528"
        else:
            self.log(tr("msg.fallback_4442"))
            self.card_type = "SLE4442"

        return self.card_type

                                                           
                                    
                                                           
    def load_card(self, card_type: str):
        if not self.conn:
            raise Exception("No active reader connection.")

        driver_cls = {
            "SLE4442": SLE4442,
            "SLE4428": SLE4428,
            "SLE5528": SLE5528,
            "SLE5542": SLE4442,
        }.get(card_type)

        if not driver_cls:
            raise Exception(tr("error.unsupported_card_type") + f": {card_type}")


        self.card = driver_cls(conn=self.conn, logger=self.log)
        self.memory = self.card.read_all()


        try:
            sm = self.card.read_security_memory()
            chv = sm[0]

            if chv == 0x7F:  
                self.card.is_authenticated = True
            else:
                self.card.is_authenticated = False

            if self.main:
                self.main.update_psc_state()

        except Exception:
            pass

        return self.memory


                                                           
                  
                                                           
    def obtain_psc(self):
        if not self.card:
            raise Exception(tr('error.no_card_loaded'))
        if self.card.is_authenticated:
            self.log(tr('msg.pin_autenthicated'))
            if self.main:
                self.main.update_psc_state()
            return None

        from drivers.sle4428 import SLE4428 as _S4428
        from drivers.sle5528 import SLE5528 as _S5528
        from drivers.sle4442 import SLE4442 as _S4442

        if isinstance(self.card, (_S4428, _S5528)):
            self.log(tr("msg.psc_recovery_not_supported"))
            psc = self.main.ask_psc_dialog()
            if not psc:
                return None
            try:
                self.card.authenticate(psc)
                self.main.update_psc_state()
                return psc
            except Exception:
                self.log(tr("error.auth_failed"))
                self.main.update_psc_state()
                return None

        if isinstance(self.card, _S4442):
            po = PinObtain(self.card, logger=self.log)
            psc = po.recover_4442()
            self.main.update_psc_state()
            return psc

        po = PinObtain(self.card, logger=self.log)
        psc = po.recover_4442()
        self.main.update_psc_state()
        return psc


                                                           
                     
                                                           
    def import_memory(self, data: bytes):

        self.memory = list(data)
        return self.memory

    def export_memory(self) -> bytes:
      
        if self.memory is None:
            raise Exception(tr("error.no_memory_export"))

        return bytes(self.memory)