
from core.language_manager import tr


class PinObtain:
   

    def __init__(self, card, logger=None):
        self.card = card
        self.log = logger if logger else (lambda msg: None)

    def _log(self, msg):
        self.log(msg)

                                                               
                                                     
                                                               
                            
     
                                                

                               
                                                          
                                                       

                             
                                                                       
                                       
                                                                
                                                                
                                      
                                                                                      
                                         

                                                    

                                                               
                                     
                                                               
    def recover_4442(self):
        self._log(tr("log.psc_recovery_safe"))

        sm = self.card.read_security_memory()
        if len(sm) < 4:
            raise Exception(tr("error.security_memory_short"))

        counter = sm[0]
        p1, p2, p3 = sm[1], sm[2], sm[3]

        self._log(
            f"{tr('log.security_memory_raw')}: {tr('log.security_counter')}={counter}, "
            f"PSC={p1:02X}-{p2:02X}-{p3:02X}"
        )

        if counter == 0:
            raise Exception(tr("error.card_is_locked"))

        if (p1, p2, p3) == (0x00, 0x00, 0x00):
                                                                         
            raise Exception(tr("log.psc_unreadable"))

        self._log(f"{tr('log.psc_visible')}: {p1:02X} {p2:02X} {p3:02X}")
        return [p1, p2, p3]
