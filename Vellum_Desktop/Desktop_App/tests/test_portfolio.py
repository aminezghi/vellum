"""Unit tests for app_pages.portfolio module and CV generation."""

from __future__ import annotations

import pandas as pd
import pytest

from app_pages import portfolio
from app_pages import researchers


class TestPortfolio:
    def test_metrics_for_calculation(self):
        df = pd.DataFrame([
            {"title": "Paper 1", "cited_by": 10, "journal": "Nature", "is_oa": True},
            {"title": "Paper 2", "cited_by": 5, "journal": "Science", "is_oa": True},
            {"title": "Paper 3", "cited_by": 3, "journal": "Nature", "is_oa": False},
            {"title": "Paper 4", "cited_by": 2, "journal": "PLOS One", "is_oa": True},
            {"title": "Paper 5", "cited_by": 1, "journal": "IEEE", "is_oa": False},
        ])
        m = portfolio.metrics_for(df)
        assert m["publications"] == 5
        assert m["citations"] == 21
        # Citations are [10, 5, 3, 2, 1]: 3 papers have >= 3 citations -> h-index = 3
        assert m["h_index"] == 3
        assert m["journals"] == 4  # Nature, Science, PLOS One, IEEE
        assert m["oa_share"] == 60.0  # 3 of 5 are OA

    def test_metrics_for_empty_dataframe(self):
        df = pd.DataFrame()
        m = portfolio.metrics_for(df)
        assert m["publications"] == 0
        assert m["citations"] == 0
        assert m["h_index"] == 0
        assert m["journals"] == 0
        assert m["oa_share"] == 0.0

    def test_to_markdown_output(self):
        prof = {
            "name": "Dr. Marie Curie",
            "affiliation": "Sorbonne University",
            "tagline": "Pioneering radioactivity research",
            "email": "curie@sorbonne.fr",
            "orcid": "0000-0002-1825-0097",
            "website": "https://curie.fr",
        }
        df = pd.DataFrame([
            {
                "title": "Radioactive Substances",
                "authors": "M. Curie",
                "journal": "Chemical News",
                "year": 1903,
                "doi": "10.1000/curie1903",
                "cited_by": 500,
                "is_oa": True,
            }
        ])
        md = portfolio.to_markdown(prof, df)
        assert "# Dr. Marie Curie" in md
        assert "Sorbonne University" in md
        assert "Radioactive Substances" in md
        assert "10.1000/curie1903" in md
        assert "h-index" in md

    def test_to_html_output(self):
        prof = {
            "name": "Alan Turing",
            "affiliation": "University of Manchester",
            "email": "turing@manchester.ac.uk",
        }
        df = pd.DataFrame([
            {
                "title": "Computing Machinery and Intelligence",
                "authors": "A. M. Turing",
                "journal": "Mind",
                "year": 1950,
                "doi": "10.1093/mind/LIX.236.433",
                "cited_by": 12000,
                "is_oa": True,
            }
        ])
        html_doc = portfolio.to_html(prof, df)
        assert "<!DOCTYPE html>" in html_doc
        assert "Alan Turing" in html_doc
        assert "Computing Machinery and Intelligence" in html_doc
        assert "10.1093/mind/LIX.236.433" in html_doc

    def test_gather_records_structure(self):
        df = portfolio._gather_records()
        assert isinstance(df, pd.DataFrame)
        expected_cols = {"title", "journal", "cited_by", "doi", "is_oa", "pdf_url", "authors", "year", "screen"}
        assert expected_cols.issubset(set(df.columns))

    def test_researchers_cv_frame_integration(self):
        # Directly verifies researchers._cv_frame() runs cleanly without ModuleNotFoundError
        df = researchers._cv_frame()
        assert isinstance(df, pd.DataFrame)

    def test_ocr_enrich_invalid_folder(self):
        res = portfolio.ocr_enrich("nonexistent_folder_xyz_123")
        assert res == 0

    def test_coerce_dataframe_inputs(self):
        # None and empty collections
        assert portfolio._coerce_dataframe(None).empty
        assert portfolio._coerce_dataframe([]).empty
        assert portfolio._coerce_dataframe(()).empty
        assert portfolio._coerce_dataframe({}).empty

        # List of records
        df_list = portfolio._coerce_dataframe([{"title": "P1", "cited_by": 5}])
        assert len(df_list) == 1
        assert df_list.iloc[0]["title"] == "P1"

        # Single record scalar dict
        df_dict = portfolio._coerce_dataframe({"title": "P2", "cited_by": 10})
        assert len(df_dict) == 1
        assert df_dict.iloc[0]["title"] == "P2"

        # Column dict
        df_cols = portfolio._coerce_dataframe({"title": ["P3"], "cited_by": [15]})
        assert len(df_cols) == 1
        assert df_cols.iloc[0]["title"] == "P3"

        # Non-collection invalid types
        assert portfolio._coerce_dataframe(12345).empty
        assert portfolio._coerce_dataframe("invalid_str").empty

    def test_sanitize_url_validation(self):
        # Dangerous pseudo-protocols rejected
        assert portfolio._sanitize_url("javascript:alert(1)") == ""
        assert portfolio._sanitize_url("JAVASCRIPT:alert('xss')") == ""
        assert portfolio._sanitize_url("data:text/html;base64,PHNjcmlwdD4=") == ""
        assert portfolio._sanitize_url("vbscript:msgbox(1)") == ""
        assert portfolio._sanitize_url("file:///etc/passwd") == ""

        # Safe protocols permitted
        assert portfolio._sanitize_url("https://example.com") == "https://example.com"
        assert portfolio._sanitize_url("http://sub.example.com/path") == "http://sub.example.com/path"
        assert portfolio._sanitize_url("mailto:researcher@sorbonne.fr") == "mailto:researcher@sorbonne.fr"

        # Domain-like strings normalized
        assert portfolio._sanitize_url("www.sorbonne.fr") == "https://www.sorbonne.fr"
        assert portfolio._sanitize_url("curie.fr") == "https://curie.fr"

        # Non-string or empty inputs
        assert portfolio._sanitize_url(None) == ""
        assert portfolio._sanitize_url(False) == ""
        assert portfolio._sanitize_url(200) == ""

    def test_metrics_for_polymorphic_and_negative(self):
        records = [
            {"title": "P1", "cited_by": -20, "is_oa": True, "journal": "Nature"},
            {"title": "P2", "cited_by": 5, "is_oa": False, "journal": "Science"},
        ]
        m = portfolio.metrics_for(records)
        assert m["publications"] == 2
        # -20 clamped to 0 -> total citations = 5
        assert m["citations"] == 5
        assert m["h_index"] == 1
        assert m["journals"] == 2
        assert m["oa_share"] == 50.0

    def test_to_html_security_and_non_strings(self):
        prof = {
            "name": 42,
            "affiliation": 100,
            "tagline": False,
            "email": "test@domain.com",
            "orcid": 9999,
            "website": "javascript:alert('xss')",
        }
        df = [
            {"title": "<b>Safe</b>", "cited_by": "<script>alert('cites')</script>", "doi": "10.1000/1"}
        ]
        html_doc = portfolio.to_html(prof, df)
        assert "javascript:" not in html_doc
        assert "<script>" not in html_doc
        assert "&lt;script&gt;" in html_doc
        assert "&lt;b&gt;Safe&lt;/b&gt;" in html_doc
        assert "42" in html_doc
        assert "100" in html_doc

    def test_ocr_enrich_safe_guards(self):
        assert portfolio.ocr_enrich(None) == 0
        assert portfolio.ocr_enrich("") == 0
        assert portfolio.ocr_enrich("   ") == 0

