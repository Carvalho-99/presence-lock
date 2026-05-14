import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog

import pystray
from PIL import Image, ImageDraw
from pystray import Menu, MenuItem

from config import LOCK_PASSWORD

_GREEN = "#22c55e"
_YELLOW = "#eab308"


def _make_icon(color: str) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=color, outline="white", width=2)
    return img


class TrayApp:
    def __init__(self, state):
        self.state = state
        self._icon: pystray.Icon | None = None
        self._timer_stop = threading.Event()
        self._timer_thread: threading.Thread | None = None

    def run(self):
        menu = Menu(
            MenuItem("Emprestar (15 min)", self._lend_15),
            MenuItem("Emprestar (30 min)", self._lend_30),
            Menu.SEPARATOR,
            MenuItem("Sair", self._quit),
        )
        self._icon = pystray.Icon(
            "presence-lock",
            _make_icon(_GREEN),
            "Presence Lock — Monitorando",
            menu,
        )
        self._icon.run()

    # --- menu handlers (pystray calls these on its own thread) ---

    def _lend_15(self, icon, item):
        threading.Thread(target=self._lend, args=(15,), daemon=True).start()

    def _lend_30(self, icon, item):
        threading.Thread(target=self._lend, args=(30,), daemon=True).start()

    def _quit(self, icon, item):
        threading.Thread(target=self._quit_with_password, daemon=True).start()

    def _quit_with_password(self):
        pwd = self._ask_password()
        if pwd is None:
            return
        if pwd != LOCK_PASSWORD:
            self._show_error("Senha incorreta.")
            return
        self._timer_stop.set()
        self._icon.stop()

    # --- lend flow ---

    def _lend(self, minutes: int):
        pwd = self._ask_password()
        if pwd is None:
            return
        if pwd != LOCK_PASSWORD:
            self._show_error("Senha incorreta.")
            return

        # Cancel any running timer before starting a new one
        self._timer_stop.set()
        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=2)
        self._timer_stop.clear()

        self.state.suspend(minutes * 60)
        self._set_icon(_YELLOW)

        self._timer_thread = threading.Thread(
            target=self._timer_loop,
            args=(minutes * 60,),
            daemon=True,
        )
        self._timer_thread.start()

    def _timer_loop(self, seconds: int):
        end_time = time.time() + seconds
        while not self._timer_stop.is_set():
            remaining = int(end_time - time.time())
            if remaining <= 0:
                break
            mins, secs = divmod(remaining, 60)
            if self._icon:
                self._icon.title = f"Presence Lock — Suspenso {mins:02d}:{secs:02d}"
            self._timer_stop.wait(1.0)

        if not self._timer_stop.is_set():
            self.state.resume()
            self._set_icon(_GREEN)
            if self._icon:
                self._icon.title = "Presence Lock — Monitorando"

    # --- helpers ---

    def _set_icon(self, color: str):
        if self._icon:
            self._icon.icon = _make_icon(color)

    def _ask_password(self) -> str | None:
        result: list[str | None] = [None]
        done = threading.Event()

        def _dialog():
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            pwd = simpledialog.askstring(
                "Presence Lock",
                "Senha para suspender o monitoramento:",
                show="*",
                parent=root,
            )
            root.destroy()
            result[0] = pwd
            done.set()

        threading.Thread(target=_dialog, daemon=True).start()
        done.wait(timeout=60)
        return result[0]

    def _show_error(self, msg: str):
        def _dialog():
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            messagebox.showerror("Presence Lock", msg, parent=root)
            root.destroy()

        threading.Thread(target=_dialog, daemon=True).start()
