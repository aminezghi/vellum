"""Unit tests for vellum_workspace module."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import vellum_workspace


class TestVellumWorkspace(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        vellum_workspace.set_vault_dir(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_vault_dir_initialization(self):
        v = vellum_workspace.get_vault_dir()
        self.assertTrue(v.exists())
        self.assertEqual(v.resolve(), Path(self.temp_dir.name).resolve())

    def test_create_and_list_projects(self):
        vellum_workspace.create_project("Meta_Analysis_2026")
        projects = vellum_workspace.list_projects()
        self.assertIn("Meta_Analysis_2026", projects)

    def test_save_and_load_project_data(self):
        p_name = "Trial_Study"
        vellum_workspace.create_project(p_name)
        data = {
            "name": p_name,
            "query": "oncology AND immunotherapy",
            "search_records": [{"title": "Paper 1", "doi": "10.1000/1"}],
            "screened": {"10.1000/1": {"status": "included"}},
        }
        vellum_workspace.save_project_data(data, name=p_name)

        loaded = vellum_workspace.load_project_data(name=p_name)
        self.assertEqual(loaded["query"], "oncology AND immunotherapy")
        self.assertEqual(len(loaded["search_records"]), 1)
        self.assertEqual(loaded["screened"]["10.1000/1"]["status"], "included")

    def test_project_stats(self):
        p_name = "Stats_Test"
        p_dir = vellum_workspace.create_project(p_name)
        # Create a dummy PDF in papers/
        dummy_pdf = p_dir / "papers" / "Smith_2020_Test.pdf"
        dummy_pdf.write_bytes(b"%PDF-1.4 dummy")

        stats = vellum_workspace.get_project_stats(p_name)
        self.assertEqual(stats["pdfs"], 1)
        self.assertIn("appraisals", stats)

    def test_user_profile_persistence(self):
        vellum_workspace.set_user_profile("Dr. Amine", "Cardiovascular AI", "deep learning, ecg")
        prof = vellum_workspace.get_user_profile()
        self.assertEqual(prof["name"], "Dr. Amine")
        self.assertEqual(prof["field"], "Cardiovascular AI")
        self.assertEqual(prof["keywords"], "deep learning, ecg")
        self.assertTrue(vellum_workspace.is_user_profile_set())


if __name__ == "__main__":
    unittest.main()
