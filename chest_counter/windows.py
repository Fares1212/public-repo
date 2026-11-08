"""OS-only APIs: key-state queries and styles on our OWN overlay window.

No process discovery, memory access, hooks, input injection or game APIs.
"""

import ctypes
from ctypes import wintypes
import hashlib


class WindowsDesktop:
    LEFT = 0x25
    CONTROL = 0x11
    SHIFT = 0x10
    WS_EX_TRANSPARENT = 0x20
    WS_EX_NOACTIVATE = 0x08000000

    def __init__(self):
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self.user32.GetAsyncKeyState.restype = ctypes.c_short
        self.user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        self.user32.GetAncestor.restype = wintypes.HWND
        # Get/SetWindowLongPtr on 64-bit Windows, WindowLong on 32-bit Windows.
        suffix = "PtrW" if ctypes.sizeof(ctypes.c_void_p) == 8 else "W"
        self.get_style = getattr(self.user32, "GetWindowLong" + suffix)
        self.set_style = getattr(self.user32, "SetWindowLong" + suffix)
        self.get_style.argtypes = [wintypes.HWND, ctypes.c_int]
        self.get_style.restype = ctypes.c_ssize_t
        self.set_style.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
        self.set_style.restype = ctypes.c_ssize_t
        self.user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int,
                                           ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        self.user32.SetWindowPos.restype = wintypes.BOOL
        self.kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        self.kernel32.CreateMutexW.restype = wintypes.HANDLE
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL
        self.mutex = None

    def acquire_instance(self, path):
        identity = hashlib.sha256(str(path.resolve()).casefold().encode()).hexdigest()[:24]
        ctypes.set_last_error(0)
        self.mutex = self.kernel32.CreateMutexW(None, False, "Local\\ChestCounter-" + identity)
        if not self.mutex:
            raise ctypes.WinError(ctypes.get_last_error())
        return ctypes.get_last_error() != 183  # ERROR_ALREADY_EXISTS

    def close(self):
        if self.mutex:
            self.kernel32.CloseHandle(self.mutex)
            self.mutex = None

    def down(self, key):
        return bool(self.user32.GetAsyncKeyState(key) & 0x8000)

    def shortcut(self, letter):
        return self.down(self.CONTROL) and self.down(self.SHIFT) and self.down(ord(letter))

    def click_through(self, widget, enabled):
        widget.update_idletasks()
        hwnd = self.user32.GetAncestor(widget.winfo_id(), 2)  # GA_ROOT; our window only
        style = self.get_style(hwnd, -20)  # GWL_EXSTYLE
        flags = self.WS_EX_TRANSPARENT | self.WS_EX_NOACTIVATE
        style = style | flags if enabled else style & ~flags
        ctypes.set_last_error(0)
        previous = self.set_style(hwnd, -20, style)
        if not previous and ctypes.get_last_error():
            raise ctypes.WinError(ctypes.get_last_error())
        # FRAMECHANGED | NOACTIVATE | NOMOVE | NOSIZE | NOZORDER
        if not self.user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x0037):
            raise ctypes.WinError(ctypes.get_last_error())
