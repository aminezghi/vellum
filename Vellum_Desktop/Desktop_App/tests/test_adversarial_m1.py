"""
Adversarial stress, boundary, and property test suite for Vellum_Desktop (Milestone M1).
Tests app_pages.portfolio bibliometrics, CV generation, escaping, and vellum_workspace path/config handling.
"""

from __future__ import annotations

import html
import os
import stat
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pytest

from app_pages import portfolio
import vellum_workspace


# ==============================================================================
# Mathematical Reference Oracle
# ==============================================================================
def oracle_h_index(citations: List[int]) -> int:
    """
    Independent ground-truth implementation of the Hirsch h-index:
    h is the maximum integer such that at least h publications have >= h citations.
    Negative citations are non-physical in bibliometrics and must be clamped to 0 or ignored.
    """
    valid_cites = [max(0, int(c)) for c in citations if isinstance(c, (int, float)) or (isinstance(c, str) and c.strip().lstrip("-").isdigit())]
    sorted_c = sorted(valid_cites, reverse=True)
    h = 0
    for i, c in enumerate(sorted_c):
        if c >= i + 1:
            h = i + 1
        else:
            break
    return h


# ==============================================================================
# Suite 1: app_pages.portfolio.metrics_for Adversarial Tests
# ==============================================================================
class TestPortfolioMetricsAdversarial:
    def test_metrics_for_none(self):
        """None should safely return zeroed metrics without crashing."""
        m = portfolio.metrics_for(None)
        assert m["publications"] == 0
        assert m["citations"] == 0
        assert m["h_index"] == 0
        assert m["journals"] == 0
        assert m["oa_share"] == 0.0

    def test_metrics_for_empty_list(self):
        """Passing an empty list [] instead of a DataFrame should not crash with AttributeError."""
        try:
            m = portfolio.metrics_for([])
            assert m["publications"] == 0
            assert m["citations"] == 0
            assert m["h_index"] == 0
        except AttributeError as e:
            pytest.fail(f"metrics_for([]) crashed with AttributeError: {e}")

    def test_metrics_for_empty_dataframe(self):
        """Empty DataFrame returns all zero metrics."""
        m = portfolio.metrics_for(pd.DataFrame())
        assert m["publications"] == 0
        assert m["citations"] == 0
        assert m["h_index"] == 0
        assert m["journals"] == 0
        assert m["oa_share"] == 0.0

    def test_metrics_for_negative_citations(self):
        """Negative citations must not produce negative total citation counts."""
        df = pd.DataFrame([
            {"title": "Paper 1", "cited_by": -10},
            {"title": "Paper 2", "cited_by": -5},
            {"title": "Paper 3", "cited_by": 10},
        ])
        m = portfolio.metrics_for(df)
        assert m["citations"] >= 0, f"Bibliometric violation: citations became negative ({m['citations']})"

    def test_metrics_for_strings_as_citations(self):
        """Non-numeric and mixed string citations should parse safely without crashing."""
        df = pd.DataFrame([
            {"title": "P1", "cited_by": "N/A"},
            {"title": "P2", "cited_by": "unknown"},
            {"title": "P3", "cited_by": ""},
            {"title": "P4", "cited_by": "42"},
            {"title": "P5", "cited_by": "  15  "},
            {"title": "P6", "cited_by": "3.14"},
            {"title": "P7", "cited_by": None},
            {"title": "P8", "cited_by": "1e2"},
        ])
        m = portfolio.metrics_for(df)
        assert m["publications"] == 8
        # "42" (42) + "15" (15) + "3.14" (3) + "1e2" (100) = 160
        assert m["citations"] == 160

    def test_single_publication_zero_citations(self):
        """Single publication with 0 citations -> h-index = 0, citations = 0."""
        df = pd.DataFrame([{"title": "P1", "cited_by": 0}])
        m = portfolio.metrics_for(df)
        assert m["publications"] == 1
        assert m["citations"] == 0
        assert m["h_index"] == 0

    def test_single_publication_high_citations(self):
        """Single publication with 10,000 citations -> h-index = 1, citations = 10,000."""
        df = pd.DataFrame([{"title": "P1", "cited_by": 10000}])
        m = portfolio.metrics_for(df)
        assert m["publications"] == 1
        assert m["citations"] == 10000
        assert m["h_index"] == 1

    def test_unsorted_citations_h_index_correctness(self):
        """Verify mathematical correctness of Hirsch h-index across randomized/unsorted inputs against oracle."""
        test_cases = [
            [0, 100, 5, 2, 4, 3, 0],
            [1, 1, 1, 1, 1],
            [10, 8, 5, 4, 3],
            [25, 8, 5, 3, 3],
            [0, 0, 0, 0],
            [100, 90, 80, 70, 60, 50, 40, 30, 20, 10],
            [5, 5, 5, 5, 5],
            [4, 4, 4, 4],
            [6, 5, 3, 1, 0],
        ]
        for cites in test_cases:
            df = pd.DataFrame([{"title": f"P{i}", "cited_by": c} for i, c in enumerate(cites)])
            expected_h = oracle_h_index(cites)
            m = portfolio.metrics_for(df)
            assert m["h_index"] == expected_h, f"Failed for cites {cites}: expected {expected_h}, got {m['h_index']}"


# ==============================================================================
# Suite 2: to_markdown and to_html Adversarial Tests
# ==============================================================================
class TestPortfolioExportAdversarial:
    def test_to_html_xss_in_cited_by(self):
        """Malicious XSS script tags in cited_by must NOT be injected unescaped into HTML output."""
        xss_payload = "<script>alert('xss_cites')</script>"
        df = pd.DataFrame([{"title": "Safe Title", "cited_by": xss_payload}])
        html_out = portfolio.to_html({}, df)
        assert xss_payload not in html_out, "VULNERABILITY: Raw unescaped <script> tag found in HTML from cited_by!"

    def test_to_html_xss_in_profile_fields(self):
        """Profile fields with HTML and script tags must be properly escaped."""
        prof = {
            "name": "<script>alert('name')</script>",
            "affiliation": "<img src=x onerror=alert('affil')>",
            "tagline": "<b>tag</b>",
            "email": "test@example.com<script>",
            "orcid": "0000-0002-1825-0097<script>",
            "website": "javascript:alert('xss')",
        }
        html_out = portfolio.to_html(prof, pd.DataFrame())
        assert "<script>alert('name')</script>" not in html_out
        assert "<img src=x" not in html_out
        assert "&lt;script&gt;" in html_out

    def test_to_html_non_string_profile_fields(self):
        """Non-string types (int, float, bool) in profile dict must not cause unhandled crashes."""
        prof = {
            "name": 12345,
            "affiliation": 999,
            "tagline": False,
            "email": 404,
            "orcid": 1000,
            "website": 200,
        }
        try:
            html_out = portfolio.to_html(prof, pd.DataFrame())
            assert "12345" in html_out
        except AttributeError as e:
            pytest.fail(f"to_html crashed on non-string profile values: {e}")

    def test_to_markdown_none_and_missing_fields(self):
        """to_markdown handles None fields, missing authors, and empty structures safely."""
        prof = {
            "name": None,
            "affiliation": None,
            "tagline": None,
            "email": None,
            "orcid": None,
            "website": None,
        }
        df = pd.DataFrame([
            {
                "title": None,
                "authors": None,
                "journal": None,
                "year": None,
                "doi": None,
                "cited_by": None,
            }
        ])
        md_out = portfolio.to_markdown(prof, df)
        assert "# Researcher" in md_out
        assert "Untitled" in md_out

    def test_to_markdown_malicious_characters(self):
        """Markdown output handles markdown injection and special characters cleanly."""
        prof = {"name": "[Hacked](http://evil.com)", "affiliation": "# Malicious Heading"}
        df = pd.DataFrame([{"title": "Title with *stars* and [links](http://evil.com)"}])
        md_out = portfolio.to_markdown(prof, df)
        assert "[Hacked]" in md_out

    def test_exports_with_empty_list_records(self):
        """Both to_markdown and to_html must handle an empty list [] without crashing."""
        try:
            md = portfolio.to_markdown({}, [])
            assert "# Researcher" in md
        except AttributeError as e:
            pytest.fail(f"to_markdown crashed on empty list []: {e}")

        try:
            h = portfolio.to_html({}, [])
            assert "<!DOCTYPE html>" in h
        except AttributeError as e:
            pytest.fail(f"to_html crashed on empty list []: {e}")

    def test_ocr_enrich_none_folder(self):
        """ocr_enrich(None) must return 0 instead of crashing with TypeError."""
        try:
            res = portfolio.ocr_enrich(None)
            assert res == 0
        except TypeError as e:
            pytest.fail(f"ocr_enrich(None) crashed with TypeError: {e}")


# ==============================================================================
# Suite 3: vellum_workspace Path Resolution & Error Handling Adversarial Tests
# ==============================================================================
class TestVellumWorkspaceAdversarial:
    def test_config_path_deep_nonexistent_directory(self, monkeypatch, tmp_path):
        """VELLUM_CONFIG_PATH pointing to deep non-existent path handles without crashing."""
        deep_path = tmp_path / "deep_nonexistent_dir" / "sub1" / "sub2" / "custom_config.json"
        monkeypatch.setenv("VELLUM_CONFIG_PATH", str(deep_path))

        cfg_path = vellum_workspace.get_config_path()
        assert cfg_path.resolve() == deep_path.resolve()

        # load_config on non-existent path should not crash and return defaults
        cfg = vellum_workspace.load_config()
        assert isinstance(cfg, dict)
        assert "vault_dir" in cfg
        assert "active_project" in cfg

        # save_config should create directories and succeed
        success = vellum_workspace.save_config({"active_project": "Deep_Project"})
        assert success is True
        assert deep_path.exists()

    def test_save_config_readonly_destination(self, monkeypatch, tmp_path):
        """save_config returns False safely without unhandled exception when destination is read-only."""
        readonly_dir = tmp_path / "readonly_dir"
        readonly_dir.mkdir(parents=True, exist_ok=True)
        readonly_cfg = readonly_dir / ".vellum_config.json"
        readonly_cfg.write_text('{"read": "only"}', encoding="utf-8")

        # Set read-only permissions
        os.chmod(readonly_cfg, stat.S_IREAD)
        monkeypatch.setenv("VELLUM_CONFIG_PATH", str(readonly_cfg))

        try:
            res = vellum_workspace.save_config({"active_project": "Should_Fail"})
            assert res is False, "save_config should return False when writing to a read-only destination!"
        finally:
            os.chmod(readonly_cfg, stat.S_IWRITE)

    def test_save_config_unserializable_data(self, monkeypatch, tmp_path):
        """save_config returns False safely when given non-serializable objects (sets, lambdas)."""
        test_cfg = tmp_path / "test_unserializable.json"
        monkeypatch.setenv("VELLUM_CONFIG_PATH", str(test_cfg))

        res = vellum_workspace.save_config({"invalid_set": {1, 2, 3}})
        assert res is False, "save_config should return False safely on non-serializable data!"

    def test_save_config_invalid_windows_path(self, monkeypatch):
        """save_config returns False safely when given path with invalid characters."""
        monkeypatch.setenv("VELLUM_CONFIG_PATH", "C:\\invalid\\??\\**\\config.json")
        res = vellum_workspace.save_config({"key": "val"})
        assert res is False
