from core.language_manager import tr
from drivers.base_card import BaseCard
import time


class SLE4428(BaseCard):
    def __init__(self, conn, logger=None):
        super().__init__(conn=conn, logger=logger)
        self.size = 1024
        self.is_authenticated = False
        self.main_memory = []
        self._pm_cache = None
        self.protection_bits = []

    def read_all(self):
        try:
            self.conn.transmit([0xFF, 0xA4, 0x00, 0x00, 0x01, 0x05])
        except Exception:
            pass

        data = []
        pos = 0
        while pos < self.size:
            chunk = min(128, self.size - pos)
            p1 = (pos >> 8) & 0xFF
            p2 = pos & 0xFF
            apdu = [0xFF, 0xB0, p1, p2, chunk]
            data.extend(self.tx(apdu, f"{tr('log.read')}[{pos}:{chunk}]"))
            pos += chunk

        self.main_memory = data
        return data

    def read_protection_memory(self):
        if self._pm_cache is not None:
            return self._pm_cache

        pm = bytearray()
        for page in range(4):
            apdu = [0xFF, 0xB2, page, 0x00, 0x20]
            pm.extend(self.tx(apdu, f"{tr('log.read_prot_page')} {page}"))

        self._pm_cache = bytes(pm)
        self._decode_protection_bits()
        return self._pm_cache

    def read_protection_map(self):
        return self.read_protection_memory()

    def _decode_protection_bits(self):
        bits = []
        for b in self._pm_cache:
            for bit in range(0, 8):
                bit_val = (b >> bit) & 1
                is_protected = (bit_val == 0)
                bits.append(is_protected)
        self.protection_bits = bits

    def authenticate(self, psc):
        if len(psc) != 2:
            raise ValueError(tr("error.psc_must_be_2bytes"))
        apdu = [0xFF, 0x20, 0x00, 0x00, 2] + list(psc)
        self.tx(apdu, tr("log.auth_4428"))
        self.is_authenticated = True

    def write_bytes(self, addr, data):
        if not self.is_authenticated:
            raise Exception(tr("msg.psc_required"))

        if not self.main_memory:
            raise Exception(tr("msg.read_card_first"))

        new = list(data)
        old = self.main_memory

        pos = addr
        off = 0
        size = len(new)

        while off < size:
            chunk = new[off: off + 16]
            old_chunk = old[pos: pos + len(chunk)]

            if chunk != old_chunk:
                apdu = [0xFF, 0xD0, (pos >> 8) & 0xFF, pos & 0xFF, len(chunk)] + chunk
                self.tx(apdu, f"{tr('log.write')}[{pos}]")
                for i, b in enumerate(chunk):
                    idx = pos + i
                    if 0 <= idx < len(self.main_memory):
                        self.main_memory[idx] = b
                time.sleep(0.2)

            pos += len(chunk)
            off += len(chunk)


    def _protect_range(self, start, length):
        if not self.main_memory or len(self.main_memory) < start + length:
            raise Exception(tr("msg.read_card_first"))

        end = start + length
        pos = start
        while pos < end:
            chunk_len = min(16, end - pos)
            chunk = list(self.main_memory[pos: pos + chunk_len])
            p1 = (pos >> 8) & 0xFF
            p2 = pos & 0xFF
            apdu = [0xFF, 0xD1, p1, p2, chunk_len] + chunk
            self.tx(apdu, f"{tr('log.protect')}[{pos}:{chunk_len}]")
            pos += chunk_len

    def set_protection_bits(self, indices):
        if not self.is_authenticated:
            raise Exception(tr("msg.psc_required"))

        if not indices:
            return

        self.read_all()
        self.read_protection_memory()

        protected = self.protection_bits
        todo = sorted({i for i in indices if 0 <= i < len(protected) and not protected[i]})
        if not todo:
            return

        start = todo[0]
        end = todo[0]

        for i in todo[1:] + [None]:
            if i is not None and i == end + 1:
                end = i
                continue

            length = end - start + 1
            chunk = self.main_memory[start:start+length]

            p1 = (start >> 8) & 0xFF
            p2 = start & 0xFF

            apdu = [0xFF, 0xD1, p1, p2, length] + chunk
            self.tx(apdu, f"{tr('log.protect')}[{start}:{length}]")

            if i is not None:
                start = end = i

        self._pm_cache = None
        self.read_protection_memory()