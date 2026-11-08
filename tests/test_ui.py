"""Run with DISPLAY set on Linux, or in a Windows desktop session."""

import os
from pathlib import Path
import sys
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from chest_counter.app import Overlay
from chest_counter.state import Counter, Store


class FakeDesktop:
    def __init__(self):
        self.count_pressed = False
        self.keys = set()
        self.locked = False

    def count_down(self):
        return self.count_pressed

    def shortcut(self, key):
        return key in self.keys

    def click_through(self, widget, enabled):
        self.locked = enabled


@unittest.skipUnless(sys.platform == "win32" or os.environ.get("DISPLAY"), "Desktop display required")
class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = tk.Tk()
        self.addCleanup(self.destroy)
        self.store = Store(Path(self.temp.name) / "counts.json")
        self.desktop = FakeDesktop()
        self.app = Overlay(self.root, self.store, Counter(), self.desktop)
        self.root.update()

    def destroy(self):
        try:
            # Cancel timers before destroying Tcl commands to keep repeated tests clean.
            for timer in self.root.tk.call("after", "info"):
                self.root.after_cancel(timer)
            self.root.destroy()
        except tk.TclError:
            pass

    def click(self, x, y):
        self.app.canvas.event_generate("<Motion>", x=x, y=y)
        self.app.canvas.event_generate("<Button-1>", x=x, y=y)
        self.app.canvas.event_generate("<ButtonRelease-1>", x=x, y=y)
        self.root.update()

    def test_real_add_and_undo_buttons_persist(self):
        self.click(110, 443)
        self.assertEqual(self.store.load().lifetime, 1)
        self.click(320, 443)
        self.assertEqual(self.store.load().lifetime, 0)

    def test_polling_counts_one_per_press_in_background(self):
        self.desktop.count_pressed = True
        for _ in range(5):
            self.app.poll()
        self.assertEqual(self.app.state.lifetime, 1)
        self.desktop.count_pressed = False
        self.app.poll()
        self.desktop.count_pressed = True
        self.app.poll()
        self.assertEqual(self.store.load().lifetime, 2)

    def test_paused_held_key_does_not_count_when_resumed(self):
        self.app.toggle_pause()
        self.desktop.count_pressed = True
        self.app.poll()
        self.app.toggle_pause()
        self.app.poll()
        self.assertEqual(self.app.state.lifetime, 0)
        self.desktop.count_pressed = False
        self.app.poll()
        self.desktop.count_pressed = True
        self.app.poll()
        self.assertEqual(self.app.state.lifetime, 1)

    def test_shortcuts_pause_lock_and_resize_once_per_press(self):
        self.desktop.keys = {"P", "L", "M"}
        self.app.poll()
        self.root.update_idletasks()
        self.assertTrue(self.app.paused)
        self.assertTrue(self.app.compact)
        self.assertFalse(self.app.locked)  # resizing deliberately unlocks the overlay
        self.assertEqual(self.root.winfo_height(), 84)
        self.app.poll()
        self.assertTrue(self.app.compact)
        self.desktop.keys.clear()
        self.app.poll()
        self.desktop.keys = {"L"}
        self.app.poll()
        self.assertTrue(self.desktop.locked)
        self.assertTrue(self.app.locked)

    def test_save_failure_rolls_back_count_and_pauses(self):
        self.app.add()
        with patch.object(self.store, "save", side_effect=OSError("No disk space")), \
                patch("chest_counter.app.messagebox.showerror") as error:
            self.app.add()
        self.assertEqual(self.app.state.lifetime, 1)
        self.assertEqual(self.store.load().lifetime, 1)
        self.assertTrue(self.app.paused)
        error.assert_called_once()

    def test_compact_contains_only_number_then_real_chest_image(self):
        for _ in range(9):
            self.app.state.add()
        self.app.toggle_compact()
        self.root.update_idletasks()
        canvas = self.app.canvas
        items = canvas.find_all()
        self.assertEqual([canvas.type(item) for item in items], ["text", "image"])
        self.assertEqual(canvas.itemcget(items[0], "text"), "9")
        self.assertGreater(canvas.bbox(items[1])[0], canvas.bbox(items[0])[2])
        self.assertGreater(self.app.compact_chest.width(), 0)
        self.assertLessEqual(canvas.bbox(items[1])[2], self.root.winfo_width())
        self.app.toggle_pause()
        self.assertEqual(len(canvas.find_all()), 2)

    def test_compact_grows_for_large_counts_and_can_return_to_controls(self):
        self.app.toggle_compact()
        self.root.update_idletasks()
        small_width = self.root.winfo_width()
        self.app.state.session = 123456
        self.app.render()
        self.root.update_idletasks()
        self.assertGreater(self.root.winfo_width(), small_width)
        self.app.canvas.event_generate("<Button-3>", x=20, y=40)
        self.root.update()
        self.assertFalse(self.app.compact)
        self.assertEqual((self.root.winfo_width(), self.root.winfo_height()), (400, 590))

    def test_new_session_requires_confirmation_and_keeps_lifetime(self):
        self.app.add()
        with patch("chest_counter.app.messagebox.askyesno", return_value=False):
            self.app.new_session()
        self.assertEqual(self.app.state.session, 1)
        with patch("chest_counter.app.messagebox.askyesno", return_value=True):
            self.app.new_session()
        restored = self.store.load()
        self.assertEqual((restored.session, restored.lifetime, restored.best), (0, 1, 1))

    def test_goal_dialog_persists_setting(self):
        with patch("chest_counter.app.simpledialog.askinteger", return_value=50):
            self.app.set_goal()
        self.assertEqual(self.store.load().goal, 50)

    def test_header_can_be_dragged_but_button_does_not_drag(self):
        from types import SimpleNamespace
        self.app.canvas.event_generate("<Motion>", x=80, y=60)
        self.root.update()
        self.app.drag_start(SimpleNamespace(x=80, y=60, x_root=100, y_root=100))
        self.assertIsNotNone(self.app.drag)
        self.app.drag = None
        self.app.canvas.event_generate("<Motion>", x=285, y=35)
        self.root.update()
        self.app.drag_start(SimpleNamespace(x=285, y=35, x_root=100, y_root=100))
        self.assertIsNone(self.app.drag)
