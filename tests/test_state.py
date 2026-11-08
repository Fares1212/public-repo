from dataclasses import asdict
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from chest_counter.state import Counter, PressEdge, Store


class CounterTests(unittest.TestCase):
    def test_session_reset_preserves_overall_and_daily_counts(self):
        state = Counter()
        for _ in range(3):
            state.add()
        state.new_session()
        state.add()
        self.assertEqual((state.session, state.lifetime, state.today, state.best), (1, 4, 4, 3))
        self.assertEqual(state.completed_sessions, 1)
        state.new_session()
        state.new_session()
        self.assertEqual(state.completed_sessions, 2)  # empty sessions aren't counted

    def test_undo_cannot_remove_counts_from_a_previous_session(self):
        state = Counter()
        state.add()
        state.new_session()
        self.assertFalse(state.undo())
        self.assertEqual(state.lifetime, 1)

    def test_undo_adjusts_best_for_active_session(self):
        state = Counter()
        state.add()
        state.add()
        self.assertEqual(state.best, 2)
        state.undo()
        self.assertEqual((state.session, state.lifetime, state.today, state.best), (1, 1, 1, 1))
        state.undo()
        self.assertFalse(state.undo())
        self.assertEqual(state.session, 0)

    def test_midnight_and_undo_do_not_make_daily_total_negative(self):
        state = Counter()
        state.add("2026-11-07")
        state.add("2026-11-08")
        state.undo("2026-11-08")
        state.undo("2026-11-08")
        self.assertEqual((state.session, state.lifetime, state.today), (0, 0, 0))

    def test_undo_history_is_bounded_and_keeps_exact_totals(self):
        state = Counter()
        for _ in range(105):
            state.add()
        for _ in range(100):
            self.assertTrue(state.undo())
        self.assertFalse(state.undo())
        self.assertEqual((state.session, state.lifetime, state.today), (5, 5, 5))

    def test_invalid_data_is_rejected(self):
        for updates in ({"session": -1}, {"today": True}, {"goal": 0}, {"session": 2},
                        {"undo_days": [date.today().isoformat()]}, {"day": "not-a-date"},
                        {"version": 2}, {"unknown": 1}):
            with self.subTest(updates=updates), self.assertRaises((ValueError, TypeError)):
                Counter.from_dict({**asdict(Counter()), **updates})


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / "nested" / "state.json")

    def test_first_launch_and_restart_restore_counts_goal_and_undo(self):
        state = self.store.load()
        state.add()
        state.add()
        state.goal = 50
        self.store.save(state)
        restored = self.store.load()
        self.assertEqual(asdict(restored), asdict(state))
        restored.undo()
        self.store.save(restored)
        self.assertEqual(self.store.load().lifetime, 1)

    def test_load_rolls_over_old_daily_count(self):
        state = Counter()
        state.add("2000-01-01")
        self.store.save(state)
        restored = self.store.load()
        self.assertEqual(restored.today, 0)
        self.assertEqual(restored.lifetime, 1)

    def test_failed_replace_leaves_previous_save_and_cleans_temp(self):
        state = Counter()
        state.add()
        self.store.save(state)
        previous = self.store.path.read_bytes()
        state.add()
        with patch("chest_counter.state.os.replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.store.save(state)
        self.assertEqual(self.store.path.read_bytes(), previous)
        self.assertEqual(list(self.store.path.parent.glob("*.tmp")), [])

    def test_corrupt_save_is_never_overwritten_on_load(self):
        self.store.path.parent.mkdir(parents=True)
        self.store.path.write_text("broken", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            self.store.load()
        self.assertEqual(self.store.path.read_text(), "broken")


class KeyTests(unittest.TestCase):
    def test_held_key_counts_only_once_then_rearms_after_release(self):
        edge = PressEdge()
        result = [edge.update(down) for down in (False, True, True, True, False, True, False)]
        self.assertEqual(result, [False, True, False, False, False, True, False])


if __name__ == "__main__":
    unittest.main()
