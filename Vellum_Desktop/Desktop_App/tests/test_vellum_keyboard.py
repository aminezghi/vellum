"""Tests for the global keyboard shortcuts and the shared screening actions.

These exist because the shortcut and the on-screen button used to be two
separate code paths, and the button carried a label - "(I)", "(E)", "(U)" -
that promised a shortcut the application did not implement. A test that only
checked the labels would have passed then, too.

What is asserted here is the behaviour: the shortcut map, the shared handler,
and the fact that both routes reach the same function.
"""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime
from unittest.mock import patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import vellum_keyboard as VK  # noqa: E402
from app_pages import screening as AS  # noqa: E402


def _candidate(cid: str, decision: str = "pending") -> dict:
    return {
        "id": cid,
        "title": f"Paper {cid}",
        "authors": ["Tester"],
        "year": 2024,
        "journal": "Journal of Testing",
        "doi": f"10.1000/{cid}",
        "abstract": "An abstract.",
        "decision": decision,
        "source_origin": "Test",
    }


class TestScreeningShortcuts(unittest.TestCase):
    """The shortcut map and the buttons must not be able to disagree."""

    def test_shortcut_map_covers_every_documented_key(self):
        self.assertEqual(
            AS.SCREENING_SHORTCUTS,
            {"i": "include", "e": "exclude", "u": "undo", "s": "skip"},
        )

    def test_shortcut_labels_match_the_shortcut_map(self):
        """The button labels are what teach the shortcut, so they must agree."""
        import inspect
        src = inspect.getsource(AS.render)
        for key, action in AS.SCREENING_SHORTCUTS.items():
            expected_label = {
                "include": "Include (I)",
                "exclude": "Exclude (E)",
                "undo": "Undo (U)",
                "skip": "Skip (S)",
            }[action]
            self.assertIn(expected_label, src, f"button label for {action!r} is missing")
            self.assertEqual(key.upper(), expected_label.split("(")[-1].rstrip(")"))

    def test_reserved_keys_are_never_bound(self):
        """A shortcut must never shadow Enter, Escape, Tab or the arrows."""
        for reserved in ("enter", "escape", "tab", " "):
            self.assertIn(reserved, VK._RESERVED)

    def test_reserved_keys_are_filtered_out_of_a_requested_map(self):
        import json
        payload = json.loads(json.dumps({"map": {"i": "include", "enter": "nope"}}))
        filtered = {k.lower(): v for k, v in payload["map"].items() if k.lower() not in VK._RESERVED}
        self.assertIn("i", filtered)
        self.assertNotIn("enter", filtered)


class TestApplyScreeningAction(unittest.TestCase):
    """The one handler behind both the button and the shortcut."""

    def setUp(self):
        self.saved = []
        self.session = {"consecutive_excludes": 0}
        self.candidates = [_candidate("a"), _candidate("b")]

    def _apply(self, action, history=None):
        history = history if history is not None else []
        with patch.object(AS, "save_screening_sessions", self.saved.append):
            result = AS.apply_screening_action(
                action, self.session, self.candidates, history, [{"id": "s"}]
            )
        return result, history

    def test_include_marks_the_first_pending_candidate(self):
        result, history = self._apply("include")
        self.assertEqual(result[0]["decision"], "included")
        self.assertEqual(result[1]["decision"], "pending")
        self.assertEqual(history, [{"id": "a", "decision": "included"}])
        self.assertEqual(self.session["consecutive_excludes"], 0)
        self.assertTrue(self.saved, "the session must be persisted")

    def test_include_records_a_timestamp(self):
        result, _ = self._apply("include")
        self.assertIn("screened_at", result[0])
        datetime.fromisoformat(result[0]["screened_at"])

    def test_exclude_marks_the_candidate_and_counts_the_streak(self):
        result, history = self._apply("exclude")
        self.assertEqual(result[0]["decision"], "excluded")
        self.assertEqual(history, [{"id": "a", "decision": "excluded"}])
        self.assertEqual(self.session["consecutive_excludes"], 1)

    def test_undo_puts_the_last_decision_back_in_the_queue(self):
        self.session["consecutive_excludes"] = 1
        history = [{"id": "a", "decision": "excluded"}]
        result, history = self._apply("undo", history)
        self.assertEqual(result[0]["decision"], "pending")
        self.assertEqual(history, [])

    def test_undo_with_no_history_is_a_no_op(self):
        result, history = self._apply("undo", [])
        self.assertEqual(result[0]["decision"], "pending")
        self.assertEqual(history, [])

    def test_skip_moves_the_candidate_to_the_back(self):
        result, _ = self._apply("skip")
        self.assertEqual(result[1]["id"], "a")
        self.assertEqual(result[0]["id"], "b")

    def test_unknown_action_changes_nothing(self):
        result, history = self._apply("something-else")
        self.assertEqual(result[0]["decision"], "pending")
        self.assertEqual(history, [])

    def test_action_with_no_pending_candidate_is_a_no_op(self):
        self.candidates = [_candidate("a", decision="included")]
        result, history = self._apply("include")
        self.assertEqual(result[0]["decision"], "included")
        self.assertEqual(history, [])


class TestKeyboardCapture(unittest.TestCase):
    """The Python side of the shortcut component."""

    def test_capture_returns_none_outside_a_browser_session(self):
        with patch.object(VK, "_runtime_available", return_value=False):
            self.assertIsNone(VK.capture({"i": "include"}))

    def test_capture_ignores_an_empty_shortcut_map(self):
        with patch.object(VK, "_runtime_available", return_value=True):
            self.assertIsNone(VK.capture({}))

    def test_a_repeated_value_is_only_handled_once(self):
        """The component keeps returning its last value, so the same press
        must not be applied twice - but two presses of the same key must be."""
        # The guard itself is pure, so it can be checked without a session.
        self.assertTrue(VK._is_new_press(1000, None))
        self.assertFalse(VK._is_new_press(1000, 1000))
        self.assertFalse(VK._is_new_press(1000, 2000))
        self.assertTrue(VK._is_new_press(2000, 1000))

        # And the end-to-end path, with the session state replaced by a dict
        # (Streamlit's own session state does not work outside `streamlit run`).
        fake_state: dict = {}
        with patch.object(VK.st, "session_state", fake_state), \
             patch.object(VK, "_runtime_available", return_value=True):
            with patch.object(VK, "_component", return_value={"action": "include", "key": "i", "ts": 1000}):
                self.assertEqual(VK.capture({"i": "include"}), "include")
                # The same press again must be ignored.
                self.assertIsNone(VK.capture({"i": "include"}))
            # A newer press of the same key must be handled.
            with patch.object(VK, "_component", return_value={"action": "include", "key": "i", "ts": 2000}):
                self.assertEqual(VK.capture({"i": "include"}), "include")

    def test_clear_forgets_the_last_handled_press(self):
        fake_state: dict = {}
        with patch.object(VK.st, "session_state", fake_state), \
             patch.object(VK, "_runtime_available", return_value=True), \
             patch.object(VK, "_component", return_value={"action": "include", "key": "i", "ts": 5000}):
            self.assertEqual(VK.capture({"i": "include"}), "include")
            self.assertIn("_vellum_keyboard_last_stamp", fake_state)
            VK.clear()
            self.assertNotIn("_vellum_keyboard_last_stamp", fake_state)


class TestKeyboardComponentAssets(unittest.TestCase):
    """The component's frontend has to travel with the frozen bundle."""

    def test_component_directory_ships_with_the_app(self):
        from pathlib import Path
        html = Path(BASE_DIR) / "keyboard_component" / "index.html"
        self.assertTrue(html.is_file(), "keyboard_component/index.html is missing")
        source = html.read_text(encoding="utf-8")
        # The listener must ignore keystrokes aimed at text fields, and it
        # must not swallow browser shortcuts.
        self.assertIn("isEditable", source)
        self.assertIn("ctrlKey", source)
        self.assertIn("aria-modal", source)
        self.assertIn("streamlit:setComponentValue", source)

    def test_packaging_ships_the_component_directory(self):
        import vellum_packaging
        self.assertIn("keyboard_component", vellum_packaging.TREES)
        self.assertIn("vellum_keyboard.py", vellum_packaging.MODULES)


if __name__ == "__main__":
    unittest.main()
