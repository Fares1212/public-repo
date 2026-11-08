"""Run with python main.py. Windows is required for background key counting."""

import argparse
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox

from chest_counter.state import Store, default_state_path


def main():
    parser = argparse.ArgumentParser(description="Standalone manual chest counter overlay")
    parser.add_argument("--data-file", type=str, help="Use a different local counter save file")
    args = parser.parse_args()
    root = tk.Tk()
    root.withdraw()
    desktop = None
    try:
        if sys.platform == "win32":
            from chest_counter.windows import WindowsDesktop
            desktop = WindowsDesktop()
            if not desktop.acquire_instance(Path(args.data_file) if args.data_file else default_state_path()):
                messagebox.showinfo("Already running", "Chest Counter is already running for this save file.", parent=root)
                return 0
        store = Store(args.data_file or default_state_path())
        try:
            state = store.load()
        except (OSError, ValueError, TypeError) as error:
            messagebox.showerror("Cannot load saved counts", f"Your save file has been left unchanged.\n{store.path}\n\n{error}", parent=root)
            return 1
        from chest_counter.app import Overlay
        Overlay(root, store, state, desktop)
        root.deiconify()
        root.mainloop()
        return 0
    finally:
        if desktop:
            desktop.close()
        try:
            root.destroy()
        except tk.TclError:
            pass


if __name__ == "__main__":
    sys.exit(main())
