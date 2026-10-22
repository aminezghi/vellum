"""Unit tests for vellum_desktop desktop app wrapper."""

from __future__ import annotations

import unittest
from pathlib import Path

from vellum_desktop import (
    find_free_port,
    check_server_health,
    VellumDesktopApp,
)


class TestVellumDesktop(unittest.TestCase):
    def test_find_free_port(self):
        port = find_free_port(9100)
        self.assertIsInstance(port, int)
        self.assertGreaterEqual(port, 9100)

    def test_check_server_health_inactive(self):
        # A random high unassigned port should return False
        self.assertFalse(check_server_health(59999))

    def test_app_script_resolution(self):
        app = VellumDesktopApp()
        script = app._find_app_script()
        self.assertTrue(script.exists())
        self.assertEqual(script.name, "pdf_downloader_app.py")


if __name__ == "__main__":
    unittest.main()
