"""
test_vellum_notes.py — Unit tests for the Research Notes & Synthesis Hub and folder browsing.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import vellum_workspace as VW
import vellum_paths as VP


class TestVellumNotes(unittest.TestCase):
    def setUp(self):
        self.project_name = "Notes_Test_Project"
        VW.create_project(self.project_name)

    def test_project_synthesis_notes_persistence(self):
        diary_content = "# Systematic Review Synthesis\n\nKey finding across 10 studies: robust accuracy."
        VW.save_project_notes(diary_content, self.project_name)

        loaded = VW.get_project_notes(self.project_name)
        self.assertEqual(loaded, diary_content)

        # Check that standalone synthesis_notes.md was also written
        p_dir = VW.get_project_dir(self.project_name)
        md_file = p_dir / "synthesis_notes.md"
        self.assertTrue(md_file.exists())
        self.assertEqual(md_file.read_text(encoding="utf-8"), diary_content)

    def test_paper_appraisal_notes_persistence(self):
        paper_key = "10.1186/s40537-024-01011-7"
        note_data = {
            "quality": 5,
            "takeaway": "Achieved 98.4% accuracy using transformer CNN.",
            "limitations": "Tested on single retrospective cohort only.",
            "notes": "Include in meta-analysis table 3.",
            "title": "Advances in ECG and PCG-based cardiovascular disease classification",
        }
        VW.save_paper_notes(paper_key, note_data, self.project_name)

        saved = VW.get_paper_notes(paper_key, self.project_name)
        self.assertEqual(saved.get("quality"), 5)
        self.assertEqual(saved.get("takeaway"), note_data["takeaway"])
        self.assertEqual(saved.get("limitations"), note_data["limitations"])
        self.assertEqual(saved.get("notes"), note_data["notes"])

        # Check all paper notes retrieval
        all_notes = VW.get_all_paper_notes(self.project_name)
        self.assertIn(paper_key.lower(), all_notes)

        # Check stats reflects noted count
        stats = VW.get_project_stats(self.project_name)
        self.assertGreaterEqual(stats.get("noted", 0), 1)

    def test_clean_html_helper(self):
        from app_pages.notes import _clean_html
        raw = """
        <div>
            <span>Title</span>
        </div>
        """
        cleaned = _clean_html(raw)
        self.assertNotIn("\n", cleaned)
        self.assertIn("<div> <span>Title</span> </div>", cleaned)

    def test_native_dialog_backend_defined(self):
        backend = VP.native_dialog_backend()
        self.assertIn(backend, ["macOS chooser", "Windows dialog", "zenity", "kdialog", "Tk dialog", "none"])

    def test_page_text_extraction(self):
        import vellum_analysis as VA
        test_pdf = Path(r"C:\Users\azoua\.gemini\antigravity\brain\eb1b9190-e9dc-42a2-b036-dcdf527acfef\.user_uploaded\media_1791963246270_93afeda6.pdf")
        if test_pdf.exists():
            pages = VA.page_text(test_pdf, max_pages=5)
            self.assertGreater(len(pages), 0)
            self.assertTrue(any(len(p.strip()) > 50 for p in pages))

    def test_pdf_viewer_module(self):
        import vellum_pdf_viewer as VPV
        import vellum_pdf_server as VPS
        test_pdf = Path(r"C:\Users\azoua\.gemini\antigravity\brain\eb1b9190-e9dc-42a2-b036-dcdf527acfef\.user_uploaded\media_1791963246270_93afeda6.pdf")
        if test_pdf.exists():
            b64 = VPV._get_base64_pdf(test_pdf)
            self.assertGreater(len(b64), 1000)
            url = VPS.register_pdf_for_streaming(test_pdf)
            self.assertTrue(url.startswith("http://127.0.0.1:"))

    def test_extract_all_metadata_progress_callback(self):
        import vellum_analysis as VA
        progress_calls = []
        def cb(cur, total, name):
            progress_calls.append((cur, total, name))

        p_dir = VW.get_project_dir(self.project_name) / "papers"
        p_dir.mkdir(parents=True, exist_ok=True)
        results = VA.extract_all_metadata(p_dir, recursive=False, progress_callback=cb)
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()


