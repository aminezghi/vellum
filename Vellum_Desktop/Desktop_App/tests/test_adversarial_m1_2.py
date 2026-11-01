"""
tests/test_adversarial_m1_2.py — Empirical Adversarial Stress Test Suite (Milestone M1).

Verification focus:
1. Download Queue Unification & Deduplication (persistence, get_project_stats counting, session_state sync).
2. Citation Export Fallback under PermissionError / OSError (vault exports/ preservation, graceful recovery).
3. Tailored Suggestions Timeout under simulated hangs / offline connection failure (<= 2.5s bound).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import requests

import vellum_workspace as VW
import vellum_direct_download as VDD
import vellum_citation_export as VCE
import app_pages.project_overview as PO


# ==============================================================================
# Suite 1: Download Queue Unification & Deduplication Stress Tests
# ==============================================================================
class TestQueueSynchronizationAdversarial:
    def test_queue_exact_doi_deduplication(self, tmp_path):
        """Verify adding identical DOI is rejected and queue maintains 1 item."""
        p_name = "Queue_Exact_DOI_Test"
        VW.create_project(p_name)
        VDD.clear_download_queue(p_name)

        paper1 = {"doi": "10.1038/s41586-020-2003-z", "title": "Paper One", "year": 2020}
        paper2 = {"doi": "10.1038/s41586-020-2003-z", "title": "Paper One Variant", "year": 2020}

        added1 = VDD.add_to_download_queue(paper1, p_name)
        assert added1 is True, "Initial paper addition must succeed"

        added2 = VDD.add_to_download_queue(paper2, p_name)
        assert added2 is False, "Duplicate DOI must be gracefully rejected"

        q = VDD.get_download_queue(p_name)
        assert len(q) == 1, "Queue must contain exactly one item"
        assert q[0]["doi"] == "10.1038/s41586-020-2003-z"

    def test_queue_exact_title_deduplication(self, tmp_path):
        """Verify adding identical title with different/missing DOI is rejected."""
        p_name = "Queue_Exact_Title_Test"
        VW.create_project(p_name)
        VDD.clear_download_queue(p_name)

        paper1 = {"doi": "", "title": "Deep Learning for Systematic Reviews", "year": 2024}
        paper2 = {"doi": "10.1234/dl2024", "title": "Deep Learning for Systematic Reviews", "year": 2024}

        added1 = VDD.add_to_download_queue(paper1, p_name)
        assert added1 is True

        added2 = VDD.add_to_download_queue(paper2, p_name)
        assert added2 is False, "Identical title must be rejected to prevent duplicate downloads"

        q = VDD.get_download_queue(p_name)
        assert len(q) == 1

    def test_queue_persistence_and_stats(self, tmp_path):
        """Verify queue items persist directly to project.json and get_project_stats counts them."""
        p_name = "Queue_Persistence_Test"
        VW.create_project(p_name)
        VDD.clear_download_queue(p_name)

        papers = [
            {"doi": f"10.1000/persist_{i}", "title": f"Study {i}", "year": 2020 + i, "source": "openalex"}
            for i in range(5)
        ]

        for p in papers:
            added = VDD.add_to_download_queue(p, p_name)
            assert added is True

        # Verify disk persistence in project.json
        data = VW.load_project_data(p_name)
        assert "download_queue" in data
        assert len(data["download_queue"]) == 5

        # Check schema of stored items
        first = data["download_queue"][0]
        assert first["doi"] == "10.1000/persist_0"
        assert first["status"] == "pending"
        assert "added_at" in first
        assert first["source"] == "openalex"

        # Verify get_project_stats reflects queued items
        stats = VW.get_project_stats(p_name)
        assert stats["queued"] == 5, f"Expected 5 queued items in stats, got {stats.get('queued')}"

    def test_queue_status_filtering_in_stats(self, tmp_path):
        """Verify get_project_stats only counts pending/unassigned items, ignoring completed/failed."""
        p_name = "Queue_Stats_Filter_Test"
        VW.create_project(p_name)

        data = VW.load_project_data(p_name)
        data["download_queue"] = [
            {"doi": "10.1/1", "title": "Item 1", "status": "pending"},
            {"doi": "10.1/2", "title": "Item 2", "status": ""},
            {"doi": "10.1/3", "title": "Item 3", "status": "completed"},
            {"doi": "10.1/4", "title": "Item 4", "status": "downloading"},
            {"doi": "10.1/5", "title": "Item 5", "status": "failed"},
        ]
        VW.save_project_data(data, p_name)

        stats = VW.get_project_stats(p_name)
        # Only pending and empty status should count as queued
        assert stats["queued"] == 2

    def test_clear_download_queue(self, tmp_path):
        """Verify clear_download_queue wipes project.json and resets stats."""
        p_name = "Queue_Clear_Test"
        VW.create_project(p_name)

        VDD.add_to_download_queue({"doi": "10.1/clear", "title": "Clear Me"}, p_name)
        assert len(VDD.get_download_queue(p_name)) == 1

        VDD.clear_download_queue(p_name)
        assert len(VDD.get_download_queue(p_name)) == 0
        stats = VW.get_project_stats(p_name)
        assert stats["queued"] == 0

    def test_queue_bulk_stress(self, tmp_path):
        """Stress-test adding 50 distinct items in rapid sequential succession."""
        p_name = "Queue_Bulk_Stress_Test"
        VW.create_project(p_name)
        VDD.clear_download_queue(p_name)

        for i in range(50):
            p = {"doi": f"10.1000/stress_{i:03d}", "title": f"Stress Paper {i}", "year": 2026}
            added = VDD.add_to_download_queue(p, p_name)
            assert added is True

        q = VDD.get_download_queue(p_name)
        assert len(q) == 50
        stats = VW.get_project_stats(p_name)
        assert stats["queued"] == 50

    def test_queue_downloads_api_observation(self):
        """
        Observational check on queue_downloads attribute.
        Documents that add_to_download_queue is the canonical method in VDD.
        """
        assert hasattr(VDD, "add_to_download_queue")
        # If queue_downloads is not defined, verify hasattr is False without raising unexpected exceptions
        has_alias = hasattr(VDD, "queue_downloads")
        # We record whether the alias exists for reporting
        assert has_alias is False or callable(getattr(VDD, "queue_downloads"))


# ==============================================================================
# Suite 2: Citation Export Fallback under PermissionError Stress Tests
# ==============================================================================
class TestCitationExportFallbackAdversarial:
    def test_citation_export_permission_error_downloads_dir(self, tmp_path):
        """Verify mock get_user_downloads_dir PermissionError falls back safely to vault exports/."""
        p_name = "Export_PermError_Test"
        VW.create_project(p_name)

        test_ris = "TY  - JOUR\nTI  - Robust Review Fallback\nAU  - Tester, A.\nPY  - 2026\nER  -\n"
        filename = "fallback_test.ris"

        with patch("vellum_citation_export.get_user_downloads_dir", side_effect=PermissionError("Permission Denied: ~/Downloads")):
            vault_path, dl_path = VCE.save_citation_export(filename, test_ris, p_name)

            assert dl_path is None, "dl_path must be None when Downloads directory raises PermissionError"
            assert vault_path is not None, "vault_path must be returned"
            assert vault_path.exists(), "vault export file must exist"
            assert vault_path.parent.name == "exports", "vault export must reside in exports/ folder"
            assert vault_path.read_text(encoding="utf-8") == test_ris, "Export content must match verbatim"

    def test_citation_export_permission_error_on_exists(self, tmp_path):
        """Verify user_dl.exists() raising PermissionError does not crash and returns vault path."""
        p_name = "Export_Exists_Perm_Test"
        VW.create_project(p_name)

        mock_dl = MagicMock()
        mock_dl.exists.side_effect = PermissionError("Restricted filesystem query")

        with patch("vellum_citation_export.get_user_downloads_dir", return_value=mock_dl):
            vault_path, dl_path = VCE.save_citation_export("exists_denied.bib", "@article{test, title={Foo}}", p_name)
            assert dl_path is None
            assert vault_path.exists()

    def test_citation_export_permission_error_on_write(self, tmp_path):
        """Verify target_dl.write_text raising PermissionError falls back cleanly."""
        p_name = "Export_Write_Perm_Test"
        VW.create_project(p_name)

        mock_dl = MagicMock()
        mock_dl.exists.return_value = True
        mock_target = MagicMock()
        mock_target.write_text.side_effect = PermissionError("[WinError 5] Access is denied")
        mock_dl.__truediv__.return_value = mock_target

        with patch("vellum_citation_export.get_user_downloads_dir", return_value=mock_dl):
            vault_path, dl_path = VCE.save_citation_export("write_denied.enw", "%0 Journal Article\n%T Bar", p_name)
            assert dl_path is None
            assert vault_path.exists()

    def test_citation_export_oserror_disk_full(self, tmp_path):
        """Verify target_dl.write_text raising OSError (disk full) falls back cleanly."""
        p_name = "Export_DiskFull_Test"
        VW.create_project(p_name)

        mock_dl = MagicMock()
        mock_dl.exists.return_value = True
        mock_target = MagicMock()
        mock_target.write_text.side_effect = OSError("[Errno 28] No space left on device")
        mock_dl.__truediv__.return_value = mock_target

        with patch("vellum_citation_export.get_user_downloads_dir", return_value=mock_dl):
            vault_path, dl_path = VCE.save_citation_export("disk_full.ris", "TY  - JOUR\nER  -", p_name)
            assert dl_path is None
            assert vault_path.exists()

    def test_citation_export_utf8_preservation_under_fallback(self, tmp_path):
        """Verify mathematical symbols, accents, Greek characters survive in fallback export."""
        p_name = "Export_Unicode_Test"
        VW.create_project(p_name)

        rich_content = (
            "TY  - JOUR\n"
            "TI  - Machine Learning for α-Synuclein & β-Amyloid Dynamics (95% CI [0.82, 0.94], p < 0.001)\n"
            "AU  - Müller, René\n"
            "AU  - 咲良, 田中\n"
            "AB  - Evaluation of CRISPR/Cas9 in vivo — a meta-analysis.\n"
            "ER  -\n"
        )

        with patch("vellum_citation_export.get_user_downloads_dir", side_effect=PermissionError("Blocked")):
            vault_path, dl_path = VCE.save_citation_export("unicode_test.ris", rich_content, p_name)
            assert dl_path is None
            saved_text = vault_path.read_text(encoding="utf-8")
            assert "α-Synuclein & β-Amyloid" in saved_text
            assert "Müller, René" in saved_text
            assert "咲良, 田中" in saved_text


# ==============================================================================
# Suite 3: Suggestion Fetch Timeout & Offline Resilience Stress Tests
# ==============================================================================
class TestSuggestionTimeoutAdversarial:
    def test_suggestion_fetch_hang_timeout_bounded(self):
        """
        Verify that when the upstream literature provider hangs indefinitely (simulated 10s sleep),
        _fetch_tailored_suggestions aborts after 2.0s and returns within 2.5s without hanging.
        """
        def slow_hang(*args, **kwargs):
            time.sleep(10.0)
            return [{"title": "Never Returned"}], 1

        if hasattr(PO._fetch_tailored_suggestions, "clear"):
            PO._fetch_tailored_suggestions.clear()

        with patch("litcheck_sources.search_openalex", side_effect=slow_hang):
            t0 = time.perf_counter()
            # Use unique query terms to prevent cache hits
            results = PO._fetch_tailored_suggestions(f"HangField_{time.time()}", "HangKeywords")
            t1 = time.perf_counter()

        elapsed = t1 - t0
        assert elapsed <= 2.5, f"_fetch_tailored_suggestions took {elapsed:.3f}s (must be <= 2.5s)"
        assert isinstance(results, list)
        assert len(results) == 3, f"Expected 3 fallback items, got {len(results)}"
        # Verify fallback items are non-empty dicts with titles
        for item in results:
            assert "title" in item
            assert len(item["title"]) > 5

    def test_suggestion_fetch_offline_connection_error(self):
        """Verify immediate fallback (<0.5s) when network throws ConnectionError (offline)."""
        if hasattr(PO._fetch_tailored_suggestions, "clear"):
            PO._fetch_tailored_suggestions.clear()

        with patch("litcheck_sources.search_openalex", side_effect=requests.exceptions.ConnectionError("Network is unreachable")):
            t0 = time.perf_counter()
            results = PO._fetch_tailored_suggestions(f"OfflineField_{time.time()}", "OfflineKeywords")
            t1 = time.perf_counter()

        elapsed = t1 - t0
        assert elapsed < 0.5, f"Offline ConnectionError took {elapsed:.3f}s (must be instant)"
        assert len(results) == 3

    def test_suggestion_fetch_gateway_timeout_504(self):
        """Verify immediate fallback when upstream provider returns 504 Gateway Timeout."""
        if hasattr(PO._fetch_tailored_suggestions, "clear"):
            PO._fetch_tailored_suggestions.clear()

        with patch("litcheck_sources.search_openalex", side_effect=requests.exceptions.HTTPError("504 Gateway Timeout")):
            results = PO._fetch_tailored_suggestions(f"TimeoutField_{time.time()}", "TimeoutKeywords")
            assert len(results) == 3

    def test_suggestion_fetch_empty_and_whitespace_inputs(self):
        """Verify calling with empty strings or whitespace safely defaults query and returns valid items."""
        if hasattr(PO._fetch_tailored_suggestions, "clear"):
            PO._fetch_tailored_suggestions.clear()

        # Both empty
        res1 = PO._fetch_tailored_suggestions("", "")
        assert isinstance(res1, list)
        assert len(res1) in (3, 4, 5)

        # Whitespace
        res2 = PO._fetch_tailored_suggestions("   \t  ", "   \n  ")
        assert isinstance(res2, list)
        assert len(res2) in (3, 4, 5)
