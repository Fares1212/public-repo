"""Counter state and atomic, local-only persistence. No game integration."""

from dataclasses import asdict, dataclass, field
from datetime import date
import json
import os
from pathlib import Path
import sys
import tempfile


def default_state_path():
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "ChestCounter" / "state.json"
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "chest-counter" / "state.json"


@dataclass
class Counter:
    version: int = 1
    session: int = 0
    lifetime: int = 0
    best_completed_session: int = 0
    completed_sessions: int = 0
    day: str = field(default_factory=lambda: date.today().isoformat())
    today: int = 0
    goal: int = 25
    undo_days: list[str] = field(default_factory=list)

    @property
    def best(self):
        return max(self.best_completed_session, self.session)

    def rollover(self, day=None):
        day = day or date.today().isoformat()
        if self.day != day:
            self.day, self.today = day, 0
        return day

    def add(self, day=None):
        day = self.rollover(day)
        self.session += 1
        self.lifetime += 1
        self.today += 1
        self.undo_days = (self.undo_days + [day])[-100:]

    def undo(self, day=None):
        self.rollover(day)
        if not self.undo_days:
            return False
        added_day = self.undo_days.pop()
        self.session -= 1
        self.lifetime -= 1
        if added_day == self.day:
            self.today -= 1
        return True

    def new_session(self):
        if self.session:
            self.completed_sessions += 1
            self.best_completed_session = max(self.best_completed_session, self.session)
        self.session = 0
        self.undo_days.clear()
        self.rollover()

    @classmethod
    def from_dict(cls, raw):
        if not isinstance(raw, dict) or raw.get("version") != 1:
            raise ValueError("Unsupported counter data version.")
        state = cls(**raw)
        for name in ("version", "session", "lifetime", "best_completed_session",
                     "completed_sessions", "today", "goal"):
            value = getattr(state, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"Invalid {name} in counter data.")
        if not 1 <= state.goal <= 99999:
            raise ValueError("Invalid goal in counter data.")
        if max(state.session, state.today, state.best_completed_session) > state.lifetime:
            raise ValueError("Counter totals are inconsistent.")
        date.fromisoformat(state.day)
        if not isinstance(state.undo_days, list) or len(state.undo_days) > min(100, state.session):
            raise ValueError("Invalid undo history.")
        for day in state.undo_days:
            date.fromisoformat(day)
        if state.undo_days.count(state.day) > state.today:
            raise ValueError("Daily counter and undo history are inconsistent.")
        return state


class Store:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        try:
            raw = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return Counter()
        # Invalid/unreadable data is reported, never silently overwritten.
        state = Counter.from_dict(json.loads(raw))
        state.rollover()
        return state

    def save(self, state):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        name = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             prefix=".counter-", suffix=".tmp", delete=False) as stream:
                name = stream.name
                json.dump(asdict(state), stream, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, self.path)
        finally:
            if name and os.path.exists(name):
                os.unlink(name)


class PressEdge:
    """Return True once per press, regardless of the duration of a held key."""

    def __init__(self):
        self.was_down = False

    def update(self, down):
        pressed = bool(down) and not self.was_down
        self.was_down = bool(down)
        return pressed
