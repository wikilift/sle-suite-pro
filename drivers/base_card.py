from core.language_manager import tr


class BaseCard:

    def __init__(self, conn, logger=None):
        self.conn = conn
        self.log = logger if logger else (lambda msg: None)
        self.size = 0
        self.main_memory: list[int] = []
        self.protection_memory: list[int] = []
        self.security_memory: list[int] = []
        self.is_authenticated: bool = False

    def _log(self, text: str):
        self.log(text)

    def _hex(self, arr) -> str:
        return " ".join(f"{b:02X}" for b in arr)

    def tx(self, apdu, desc: str = ""):
        self._log(f"<< {tr('log.apdu_send')} ({desc}): {self._hex(apdu)}")

        data, sw1, sw2 = self.conn.transmit(apdu)

        if sw1 != 0x90:
            msg_tr = tr("log.sw_error")
            msg = f"{msg_tr} SW={sw1:02X}{sw2:02X} en {desc}"
            self._log(f">> {msg}")
            raise Exception(msg)

        if data:
            self._log(f">> {tr('log.apdu_recv')} DATA: {self._hex(data)}")
        else:
            self._log(f">> {tr('log.sw_ok')}")

        return data

    def read_range(self, addr: int, length: int) -> list[int]:
        result: list[int] = []
        pos = addr
        remaining = length

        while remaining > 0:
            chunk = min(remaining, 240)
            apdu = [0xFF, 0xB0, 0x00, pos & 0xFF, chunk]
            data = self.tx(apdu, f"{tr('log.read_chunk')}[{pos}:{chunk}]")

            if not data:
                raise Exception(tr("msg.error_card_read"))

            result.extend(data)

            real = len(data)
            if real < chunk:
                remaining -= real
                pos += real
                continue

            remaining -= chunk
            pos += chunk

        return result

    def read_all(self) -> list[int]:
        if self.size <= 0:
            raise Exception(tr("msg.error_card_read"))

        self._log(f"{tr('log.read_full')} ({self.size} bytes)…")
        data = self.read_range(0, self.size)
        self.main_memory = data
        return data

    def read_security_memory(self) -> list[int]:
        apdu = [0xFF, 0xB1, 0x00, 0x00, 4]
        data = self.tx(apdu, tr("log.read_security"))
        self.security_memory = list(data)
        return self.security_memory

    def authenticate(self, psc: list[int]):
        if len(psc) != 3:
            raise ValueError(tr("error.pin_must_be_3bytes"))

        try:
            sm_before = self.read_security_memory()
            counter_before = sm_before[0]
            self._log(f"{tr('log.security_before_auth')}: {counter_before}")
            if counter_before == 0:
                raise Exception(tr("error.card_is_locked"))
        except Exception as e:
            self._log(f"{tr('error.cannot_guess_pin')} {e}")

        apdu = [0xFF, 0x20, 0x00, 0x00, 3] + list(psc)
        self._log(f"<< AUTH: {self._hex(apdu)}")
        data, sw1, sw2 = self.conn.transmit(apdu)
        self._log(f">> SW={sw1:02X}{sw2:02X}")

        if sw1 != 0x90:
            msg = f"{tr('error.auth_failed')}{sw1:02X}{sw2:02X}"
            self._log(msg)
            raise Exception(msg)

        sm_after = self.read_security_memory()
        self.security_memory = list(sm_after)
        counter_after = sm_after[0]
        stored_psc = sm_after[1:4]

        if stored_psc == list(psc):
            self.is_authenticated = True
            self._log(
                f"{tr('log.auth_ok')}. {tr('log.security_counter')}={counter_after}"
            )
        else:
            self.is_authenticated = False
            self._log(
                f"{tr('log.auth_fail')}. {tr('log.security_counter')}={counter_after}"
            )
         
            raise Exception(
                f"{tr('log.auth_fail')}. {tr('error.auth_fail_attempts')} {counter_after} {tr('log.security_counter')}."
            )

    def change_psc(self, new_psc: list[int]):
        if len(new_psc) != 3:
            raise ValueError(tr("error.pin_must_be_3bytes"))

        if not self.is_authenticated:
            raise Exception(tr("msg.psc_required"))

        apdu = [0xFF, 0xD2, 0x00, 0x01, 3] + list(new_psc)
        self.tx(apdu, tr("log.change_psc_ok"))

        counter = self.security_memory[0] if self.security_memory else 0
        self.security_memory = [counter] + list(new_psc)
        self._log(tr("log.change_psc_ok"))

    def write_bytes(self, addr: int, data):
        if not self.is_authenticated:
            raise Exception(tr("msg.write_blocked"))

        if addr < 0:
            raise ValueError(tr("log.write_addr"))
        if not data:
            return

        max_chunk = 16
        total_len = len(data)
        offset = 0

        while offset < total_len:
            chunk = list(data[offset:offset + max_chunk])
            chunk_len = len(chunk)
            current_addr = addr + offset

            apdu = [0xFF, 0xD0, 0x00, current_addr & 0xFF, chunk_len] + chunk
            self.tx(apdu, f"{tr('log.write_chunk')}[{current_addr}:{chunk_len}]")

            for i, b in enumerate(chunk):
                idx = current_addr + i
                if 0 <= idx < len(self.main_memory):
                    self.main_memory[idx] = b

            offset += chunk_len

    def read_protection_memory(self) -> list[int]:
        apdu = [0xFF, 0xB2, 0x00, 0x00, 4]
        data = self.tx(apdu, tr("log.read_pm"))
        self.protection_memory = data
        return data

    def protect_byte(self, addr: int):
        raise NotImplementedError(tr("log.write_protected"))
    
    def ensure_authenticated(self, main):
        
        if getattr(self, "is_authenticated", False):
            return True

        sm = self.read_security_memory()
        chv = sm[0]

        if self.__class__.__name__ == "SLE4428":
            if chv == 0x7F:
                saved = main.get_saved_psc(self)
                if saved:
                    try:
                        self.authenticate(saved)
                        return True
                    except Exception:
                        pass

                psc = main.ask_user_for_psc()
                try:
                    self.authenticate(psc)
                except Exception:
                    return False

                main.save_psc(self, psc)
                return True

            else:
                psc = main.ask_user_for_psc()
                try:
                    self.authenticate(psc)
                except Exception:
                    return False
                main.save_psc(self, psc)
                return True

        elif self.__class__.__name__ == "SLE4442":
            if chv == 0:
                main.show_error(tr("msg.psc_blocked_cannot_continue")) 
                return False

            psc = main.ask_user_for_psc()
            try:
                self.authenticate(psc)
            except Exception:
                return False
            main.save_psc(self, psc)
            return True

        return True