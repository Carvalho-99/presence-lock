import ctypes
import socket
import threading
import time

from config import MAX_MISSES, PHONE_MAC, SCAN_INTERVAL

_AF_BTH = 32
_BTPROTO_RFCOMM = 3
_PRESENT_ERRORS = {10064, 10061}


class BluetoothMonitor:
    def __init__(self, state):
        self.state = state

    def start(self):
        t = threading.Thread(target=self._run, daemon=True, name="bt-monitor")
        t.start()

    def _run(self):
        misses = 0
        while True:
            time.sleep(SCAN_INTERVAL)

            if self.state.suspended:
                misses = 0
                continue

            if self._detect():
                misses = 0
            else:
                misses += 1
                if misses >= MAX_MISSES:
                    misses = 0
                    self._lock_screen()

    def _detect(self) -> bool:
        sock = None
        try:
            sock = socket.socket(_AF_BTH, socket.SOCK_STREAM, _BTPROTO_RFCOMM)
            sock.settimeout(4.0)
            sock.connect((PHONE_MAC, 1))
            return True
        except OSError as e:
            return getattr(e, "winerror", None) in _PRESENT_ERRORS
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass

    @staticmethod
    def _lock_screen():
        ctypes.windll.user32.LockWorkStation()
