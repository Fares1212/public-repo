"""Tk overlay: all interaction is manual; no connection to Fortnite."""

from copy import deepcopy
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog

from .state import PressEdge


BG = "#0b1020"
CARD = "#131c30"
LINE = "#26324b"
TEXT = "#f3f6ff"
MUTED = "#8c9bb9"
ACCENT = "#9aff69"
GOLD = "#ffc76a"


class Overlay:
    def __init__(self, root, store, state, desktop=None):
        self.root, self.store, self.state, self.desktop = root, store, state, desktop
        self.paused = False
        self.compact = False
        self.locked = False
        self.notice = "Saved on this device"
        self.flash = False
        self.busy = False
        self.drag = None
        self.edges = {key: PressEdge() for key in ("left", "P", "L", "M", "Q")}
        if desktop:
            self.edges["left"].update(desktop.down(desktop.LEFT))
            for letter in ("P", "L", "M", "Q"):
                self.edges[letter].update(desktop.shortcut(letter))
        self.font = "Segoe UI" if sys.platform == "win32" else "Arial"
        root.title("Chest Counter")
        root.configure(bg=BG)
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.97)  # also enables the layered Windows window
        root.geometry(f"400x590+{max(20, root.winfo_screenwidth() - 430)}+80")
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.canvas = tk.Canvas(root, bg=BG, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self.drag_start)
        self.canvas.bind("<B1-Motion>", self.drag_move)
        self.canvas.bind("<ButtonRelease-1>", lambda event: setattr(self, "drag", None))
        if not desktop:
            # Other systems support UI preview only, not in-game background counting.
            for letter, action in (("p", self.toggle_pause), ("m", self.toggle_compact), ("q", self.close)):
                root.bind(f"<Control-Shift-{letter.upper()}>", lambda event, fn=action: fn())
        self.render()
        self.root.after(16, self.poll)
        self.root.after(1000, self.tick)

    def text(self, x, y, value, size=11, color=TEXT, weight="normal", anchor="w", tags=()):
        return self.canvas.create_text(x, y, text=value, fill=color, font=(self.font, -round(size * 1.3), weight),
                                       anchor=anchor, tags=tags)

    def panel(self, x, y, w, h, fill=CARD, outline=LINE, radius=14, tags=()):
        r = radius
        points = [x+r,y, x+w-r,y, x+w,y, x+w,y+r, x+w,y+h-r, x+w,y+h,
                  x+w-r,y+h, x+r,y+h, x,y+h, x,y+h-r, x,y+r, x,y]
        self.canvas.create_polygon(points, smooth=True, splinesteps=24, fill=fill,
                                   outline=outline, width=1, tags=tags)

    def button(self, name, x, y, w, h, label, action, primary=False, disabled=False):
        fill = ACCENT if primary else CARD
        color = BG if primary else TEXT
        if disabled:
            fill, color = CARD, MUTED
        self.panel(x, y, w, h, fill, fill if primary else LINE, 10, (name,))
        self.text(x+w/2, y+h/2, label, 11, color, "bold", "center", (name,))
        if not disabled:
            self.canvas.tag_bind(name, "<Button-1>", lambda event: action())
            self.canvas.tag_bind(name, "<Enter>", lambda event: self.canvas.configure(cursor="hand2"))
            self.canvas.tag_bind(name, "<Leave>", lambda event: self.canvas.configure(cursor=""))

    def chest(self, x, y, scale=1):
        def polygon(points, fill, outline):
            self.canvas.create_polygon([v*scale+(x if i % 2 == 0 else y) for i,v in enumerate(points)],
                                       fill=fill, outline=outline, width=max(1, scale))
        polygon([0,13, 32,4, 62,16, 30,26], "#e8b660", "#ffe2a2")
        polygon([0,13, 30,26, 30,54, 0,39], "#9f612e", "#e8b660")
        polygon([30,26, 62,16, 62,43, 30,54], "#ce8d3d", "#ffe2a2")
        polygon([0,23, 30,36, 62,25, 62,31, 30,42, 0,29], "#edbf6c", "#edbf6c")
        polygon([24,29, 36,27, 36,41, 24,44], "#ffe0a0", "#ffedc5")
        polygon([29,32, 32,31, 32,38, 29,39], "#70491f", "#70491f")

    def render(self):
        c = self.canvas
        c.delete("all")
        c.configure(cursor="")
        w = 320 if self.compact else 400
        h = 190 if self.compact else 590
        c.create_rectangle(0, 0, w-1, h-1, outline=LINE)
        if self.compact:
            self.text(20, 23, "CHEST COUNTER", 10, MUTED, "bold")
            self.text(20, 83, f"{self.state.session:,}", 44, ACCENT if self.flash else TEXT, "bold")
            self.text(22, 126, "THIS SESSION", 9, MUTED, "bold")
            self.text(295, 82, f"{self.state.lifetime:,}", 24, GOLD, "bold", "e")
            self.text(295, 118, "ALL TIME", 9, MUTED, "bold", "e")
            if not self.locked:
                self.button("lock", 162, 12, 47, 26, "Lock", self.toggle_lock, disabled=not self.desktop)
                self.button("expand", 219, 12, 44, 26, "+", self.toggle_compact)
                self.button("exit", 273, 12, 30, 26, "×", self.close)
            status = "PAUSED" if self.paused else "LEFT ARROW  +1"
            if not self.desktop:
                status = "UI PREVIEW · WINDOWS FOR GLOBAL KEYS"
            self.text(20, 165, status, 8, GOLD if self.paused else ACCENT, "bold")
            if self.locked:
                self.text(300, 165, "Ctrl+Shift+L", 8, MUTED, anchor="e")
            return

        self.chest(23, 20, 0.55)
        self.text(69, 30, "CHEST COUNTER", 12, TEXT, "bold")
        self.text(69, 51, "YOUR LOOT. YOUR NUMBERS.", 8, MUTED)
        self.button("pause", 267, 20, 67, 32, "Resume" if self.paused else "Pause", self.toggle_pause)
        self.button("exit", 346, 20, 32, 32, "×", self.close)

        self.panel(20, 82, 360, 217)
        self.text(40, 108, "THIS SESSION", 10, MUTED, "bold")
        self.text(38, 169, f"{self.state.session:,}", 58 if self.state.session < 10000 else 40,
                  ACCENT if self.flash else TEXT, "bold")
        self.text(42, 220, "chests opened", 12, MUTED)
        self.chest(282, 142, 1.1)
        goal_met = self.state.session >= self.state.goal
        self.text(40, 254, "GOAL REACHED!" if goal_met else "SESSION GOAL", 8,
                  ACCENT if goal_met else MUTED, "bold")
        self.text(360, 254, f"{self.state.session:,} / {self.state.goal:,}  ·  Edit", 9, MUTED, anchor="e", tags=("goal",))
        c.tag_bind("goal", "<Button-1>", lambda event: self.set_goal())
        self.panel(40, 274, 320, 5, LINE, LINE, 2)
        fraction = min(1, self.state.session / self.state.goal)
        if fraction:
            self.panel(40, 274, max(5, 320*fraction), 5, ACCENT, ACCENT, 2)

        for x, title, value, color in ((20, "ALL TIME", self.state.lifetime, GOLD),
                                       (144, "TODAY", self.state.today, TEXT),
                                       (268, "BEST SESSION", self.state.best, TEXT)):
            self.panel(x, 313, 112, 88)
            self.text(x+14, 336, title, 8, MUTED, "bold")
            self.text(x+14, 372, f"{value:,}", 22 if value < 100000 else 14, color, "bold")

        self.button("add", 20, 420, 236, 46, "+  Add chest", self.add, primary=True, disabled=self.paused)
        self.button("undo", 268, 420, 112, 46, "↶  Undo", self.undo, disabled=not self.state.undo_days)
        self.button("session", 20, 478, 174, 37, "New session", self.new_session)
        self.button("compact", 206, 478, 174, 37, "Compact overlay  ↗", self.toggle_compact)
        c.create_oval(22, 537, 28, 543, fill=GOLD if self.paused else ACCENT, outline="")
        label = "Paused · counts will not change" if self.paused else "Left Arrow  =  +1 chest"
        if not self.desktop:
            label = "UI preview · global keys require Windows"
        self.text(37, 540, label, 9, GOLD if self.paused else MUTED)
        self.text(20, 565, self.notice, 8, MUTED)
        self.text(380, 565, "Ctrl+Shift+P: pause", 8, MUTED, anchor="e")

    def change(self, operation, message):
        previous = deepcopy(self.state)
        operation()
        try:
            self.store.save(self.state)
        except OSError as error:
            self.state = previous
            self.paused = True
            self.render()
            self.busy = True
            try:
                messagebox.showerror("Counts not saved", f"Counting has been paused; this change was not applied.\n\n{error}", parent=self.root)
            finally:
                self.busy = False
            return False
        self.notice = message
        self.render()
        return True

    def add(self):
        if self.paused or self.busy:
            return
        if self.change(self.state.add, "Chest saved · press Undo to correct"):
            self.flash = True
            self.render()
            self.root.after(180, self.clear_flash)

    def clear_flash(self):
        self.flash = False
        self.render()

    def undo(self):
        if self.state.undo_days and not self.busy:
            self.change(self.state.undo, "Last chest removed from your totals")

    def new_session(self):
        self.busy = True
        try:
            proceed = not self.state.session or messagebox.askyesno(
                "Start a new session?", "Reset this session to zero?\nYour all-time and daily totals will stay saved.", parent=self.root)
            if proceed:
                self.change(self.state.new_session, "New session · all-time total kept")
        finally:
            self.busy = False

    def set_goal(self):
        self.busy = True
        try:
            goal = simpledialog.askinteger("Session goal", "How many chests is your goal?", parent=self.root,
                                           initialvalue=self.state.goal, minvalue=1, maxvalue=99999)
            if goal is not None:
                self.change(lambda: setattr(self.state, "goal", goal), "Session goal updated")
        finally:
            self.busy = False

    def toggle_pause(self):
        if not self.busy:
            self.paused = not self.paused
            self.render()

    def toggle_compact(self):
        if self.busy:
            return
        self.compact = not self.compact
        if self.locked:
            self.toggle_lock()
        self.root.geometry("320x190" if self.compact else "400x590")
        self.render()

    def toggle_lock(self):
        if not self.desktop or self.busy:
            return
        enabled = not self.locked
        try:
            self.desktop.click_through(self.root, enabled)
        except OSError as error:
            messagebox.showerror("Cannot change overlay mode", str(error), parent=self.root)
            return
        self.locked = enabled
        self.notice = "Click-through on · Ctrl+Shift+L to unlock" if self.locked else "Overlay unlocked"
        self.render()

    def poll(self):
        if self.desktop:
            actions = {"P": self.toggle_pause, "L": self.toggle_lock,
                       "M": self.toggle_compact, "Q": self.close}
            # Always update edges, even when paused or a dialog is open. Holding
            # a key while resuming must not add an unintended chest.
            pressed = self.edges["left"].update(self.desktop.down(self.desktop.LEFT))
            shortcut_presses = {letter: self.edges[letter].update(self.desktop.shortcut(letter))
                                for letter in actions}
            if not self.busy:
                for letter, action in actions.items():
                    if shortcut_presses[letter]:
                        action()
                        if letter == "Q":
                            return
                if pressed:
                    self.add()
        self.root.after(16, self.poll)

    def tick(self):
        if not self.busy:
            before = self.state.day
            self.state.rollover()
            if before != self.state.day:
                self.render()
        self.root.after(1000, self.tick)

    def drag_start(self, event):
        if self.locked:
            return
        current = self.canvas.find_withtag("current")
        if current and set(self.canvas.gettags(current[0])) - {"current"}:
            return
        if event.y < 72:
            self.drag = (event.x_root-self.root.winfo_x(), event.y_root-self.root.winfo_y())

    def drag_move(self, event):
        if self.drag:
            x, y = event.x_root-self.drag[0], event.y_root-self.drag[1]
            self.root.geometry(f"{x:+d}{y:+d}")

    def close(self):
        if not self.busy:
            self.root.destroy()
