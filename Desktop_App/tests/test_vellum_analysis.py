"""Unit tests for vellum_analysis shared services and fallbacks."""

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from vellum_analysis import (
    compute_file_hash,
    extract_pdf_metadata,
    meta_frame,
    _meta_text,
    is_ready,
)


class TestVellumAnalysis(unittest.TestCase):
    def test_is_ready(self):
        self.assertTrue(is_ready())

    def test_compute_file_hash_fallback(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Hello Vellum Academic Workbench")
            tmp_path = f.name

        try:
            h = compute_file_hash(tmp_path)
            self.assertIsInstance(h, str)
            self.assertEqual(len(h), 64)  # SHA-256 is 64 hex characters
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_meta_text_flattening(self):
        self.assertEqual(_meta_text(["Author One", "Author Two"]), "Author One; Author Two")
        self.assertEqual(_meta_text("Simple String"), "Simple String")
        self.assertEqual(_meta_text(None), "")

    def test_meta_frame_empty(self):
        df = meta_frame({})
        self.assertTrue(df.empty)


if __name__ == "__main__":
    unittest.main()
