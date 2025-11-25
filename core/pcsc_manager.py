from smartcard.System import readers
from smartcard.Exceptions import NoCardException
from core.language_manager import tr

class PCSCManager:
    
    def __init__(self, logger=None):
        self.reader = None
        self.conn = None
        self.log = logger if logger else (lambda x: None)
                                                                 
    def _log(self, msg):
        self.log(msg)

    def list_readers(self):
        try:
            r = readers()
            return r
        except Exception as e:
            self._log(f"{tr('msg.enumerating_error')}: {e}")
            return []

    def auto_select_reader(self):
        rlist = self.list_readers()
        if not rlist:
            raise Exception(tr('msg.no_readers'))

        for r in rlist:
            rn = str(r).upper()
            if "ACS" in rn or "ACR" in rn:
                self.reader = r
                self._log(f"{tr('msg.acs_detected')}: {r}")
                return r
                                  
        self.reader = rlist[0]
        self._log(f"{tr('msg.acs_no_detected')} {self.reader}")
        return self.reader

    def connect(self, reader=None):
        if reader is None:
            reader = self.auto_select_reader()

        try:
            self.conn = reader.createConnection()
            self.conn.connect()
            self._log(f"{tr('msg.connected_to')}: {reader}")
        except NoCardException:
            raise Exception(tr('msg.no_card_inserted'))
        except Exception as e:
            raise Exception(f"{tr('msg.error_connect')} {e}")

    def disconnect(self):
        if self.conn:
            try:
                self.conn.disconnect()
            except:
                pass
        self.conn = None
        self._log(tr('msg.reader_disconnected'))
         
    def get_atr(self):
        if not self.conn:
            raise Exception(tr('msg.no_connected'))
        return self.conn.getATR()
                   
    def transmit(self, apdu):
        if not self.conn:
            raise Exception(tr('error.no_active_connection'))

        try:
            data, sw1, sw2 = self.conn.transmit(apdu)
            return data, sw1, sw2
        except NoCardException:
            raise Exception(tr('error.no_card_inserted'))
        except Exception as e:
            raise Exception(f"{tr('error.transmit_apdu')} {e}")