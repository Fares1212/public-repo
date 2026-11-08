"""Validate keyboard layout selection with mocked Windows OS queries."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from chest_counter.windows import WindowsDesktop


class CountKeyTests(unittest.TestCase):
    def desktop(self, character_mapping, physical_mapping=0xC0):
        desktop = WindowsDesktop.__new__(WindowsDesktop)
        desktop.user32 = SimpleNamespace(
            VkKeyScanW=Mock(return_value=character_mapping),
            MapVirtualKeyW=Mock(return_value=physical_mapping),
            GetAsyncKeyState=Mock(return_value=0),
        )
        desktop.count_key = desktop._count_virtual_key()
        return desktop

    def test_french_layout_uses_unmodified_squared_character(self):
        desktop = self.desktop(0xDE)
        self.assertEqual(desktop.count_key, 0xDE)
        desktop.user32.VkKeyScanW.assert_called_once_with("²")
        desktop.user32.MapVirtualKeyW.assert_not_called()

    def test_layout_without_squared_character_uses_same_physical_key(self):
        desktop = self.desktop(-1)
        self.assertEqual(desktop.count_key, 0xC0)
        desktop.user32.MapVirtualKeyW.assert_called_once_with(0x29, 3)

    def test_shift_or_altgr_mapping_does_not_repurpose_another_key(self):
        for modifiers in (1, 2, 4, 6):
            with self.subTest(modifiers=modifiers):
                desktop = self.desktop((modifiers << 8) | ord("2"))
                self.assertEqual(desktop.count_key, 0xC0)
                desktop.user32.MapVirtualKeyW.assert_called_once_with(0x29, 3)

    def test_unavailable_os_mapping_retains_french_squared_key(self):
        desktop = self.desktop(-1, physical_mapping=0)
        self.assertEqual(desktop.count_key, 0xDE)

    def test_counting_queries_squared_key_instead_of_left_arrow(self):
        desktop = self.desktop(0xDE)
        desktop.user32.GetAsyncKeyState.side_effect = lambda key: 0x8000 if key == 0x25 else 0
        self.assertFalse(desktop.count_down())
        desktop.user32.GetAsyncKeyState.assert_called_once_with(0xDE)
        desktop.user32.GetAsyncKeyState.return_value = 0x8000
        desktop.user32.GetAsyncKeyState.side_effect = None
        self.assertTrue(desktop.count_down())

    def test_old_keypress_flag_is_not_treated_as_a_held_key(self):
        desktop = self.desktop(0xDE)
        desktop.user32.GetAsyncKeyState.return_value = 1
        self.assertFalse(desktop.count_down())


if __name__ == "__main__":
    unittest.main()
