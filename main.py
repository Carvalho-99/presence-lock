import threading
import time


class AppState:
    def __init__(self):
        self._lock = threading.Lock()
        self._suspended_until: float = 0.0

    @property
    def suspended(self) -> bool:
        with self._lock:
            return time.time() < self._suspended_until

    def suspend(self, seconds: int):
        with self._lock:
            self._suspended_until = time.time() + seconds

    def resume(self):
        with self._lock:
            self._suspended_until = 0.0


def main():
    from monitor import BluetoothMonitor
    from tray import TrayApp

    state = AppState()

    monitor = BluetoothMonitor(state)
    monitor.start()

    tray = TrayApp(state)
    tray.run()  # blocks until user clicks Sair


if __name__ == "__main__":
    main()
