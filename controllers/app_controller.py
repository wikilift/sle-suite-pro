                               
                        

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

        self.conn = None
        self.connected_reader = None
        self.card = None
        self.memory = None

                                                               
                       
                                                               
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

        except Exception as e:
            self.conn = None
            self.connected_reader = None
            raise e

    def disconnect_reader(self):
        if self.conn:
            try:
                self.conn.disconnect()
            except:
                pass
        self.conn = None
        self.connected_reader = None
        self.card = None
        self.memory = None

                                                               
                    
                                                               
    def detect_card_type(self):
        if not self.conn:
            raise Exception("No active reader connection.")

        atr = self.conn.getATR()
        ctype = ATRDetector.detect(atr, self.conn, logger=self.log)

                       
        if ctype == CardType.SLE4442:
            return "SLE4442"
        if ctype == CardType.SLE5542:
            return "SLE5542"
        if ctype == CardType.SLE4428:
            return "SLE4428"
        if ctype == CardType.SLE5528:
            return "SLE5528"

        self.log("Tipo no reconocido, usando fallback SLE4442.")
        return "SLE4442"



                                                               
                             
                                                               
                                   

    def load_card(self, card_type):
        if not self.conn:
            raise Exception("No active reader connection.")

        driver = {
            "SLE4442": SLE4442,
            "SLE4428": SLE4428,
            "SLE5528": SLE5528,
            "SLE5542": SLE4442,
        }.get(card_type)

        if not driver:
            raise Exception(f"Unsupported card type: {card_type}")

                                                      
        self.card = driver(
            conn=self.conn,
            logger=self.log
        )

        self.memory = self.card.read_all()
        return self.memory


                                                               
                
                                                               
    def obtain_psc(self):
        if not self.card:
            raise Exception("No card loaded.")

        po = PinObtain(self.card, logger=self.log)

                                           
        if isinstance(self.card, (SLE4428, SLE5528)):
            return po.brute_2byte()

                                                                 
                                                                                
        return po.recover_4442()

                                                               
                     
                                                               
    def import_memory(self, data: bytes):
      
        self.memory = list(data)
        return self.memory

    def export_memory(self):
        if not self.memory:
            raise Exception("No memory to export.")
        return bytes(self.memory)
