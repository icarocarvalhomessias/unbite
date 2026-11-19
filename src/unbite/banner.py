"""A red banner on top of every window, plus a short sound."""

from __future__ import annotations

import sys
import tkinter as tk

_FONT = {"win32": "Segoe UI", "darwin": "Helvetica Neue"}.get(sys.platform, "DejaVu Sans")
_RED = "#c62828"


class Banner:
    def __init__(self, root: tk.Tk, text: str, sound: bool = True) -> None:
        self._root = root
        self._text = text
        self._sound = sound
        self._window: tk.Toplevel | None = None

    def show(self, seconds: float = 1.5) -> None:
        if self._sound:
            self._root.bell()
        if self._window is not None:
            return
        window = tk.Toplevel(self._root)
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        window.configure(bg=_RED)
        label = tk.Label(
            window,
            text=f"✋  {self._text}",
            fg="white",
            bg=_RED,
            font=(_FONT, 26, "bold"),
            padx=36,
            pady=28,
        )
        label.pack()
        window.update_idletasks()
        x = (window.winfo_screenwidth() - window.winfo_reqwidth()) // 2
        window.geometry(f"+{x}+60")
        self._window = window
        self._root.after(int(seconds * 1000), self.hide)

    def hide(self) -> None:
        if self._window is not None:
            self._window.destroy()
            self._window = None
