from PySide6.QtCore import QObject, Signal, Slot

class CardWorker(QObject):
    finished = Signal(object)
    error = Signal(str)
    log = Signal(str)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    @Slot()
    def read_card(self):
        try:
            ctype = self.controller.detect_card_type()
            self.log.emit(f"Tipo de tarjeta: {ctype}")
            data = self.controller.load_card(ctype)
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))

    @Slot(list)
    def authenticate(self, psc):
        try:
            card = self.controller.card
            card.authenticate(psc)
            self.finished.emit(True)
        except Exception as e:
            self.error.emit(str(e))

    @Slot(int, list)
    def write_bytes(self, addr, data):
        try:
            card = self.controller.card
            card.write_bytes(addr, data)
            self.finished.emit(True)
        except Exception as e:
            self.error.emit(str(e))
