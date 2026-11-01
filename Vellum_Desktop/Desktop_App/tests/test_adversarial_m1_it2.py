"""
tests/test_adversarial_m1_it2.py — Challenger M1 Iteration 2 Adversarial Stress Suite.

Empirical verification of:
1. Re-verification of all 6 previous defects from M1 iteration 1.
2. Advanced XSS payloads in cited_by and profile fields (nested tags, event handlers, attribute breakout).
3. Malicious URL schemes in website (javascript, data, vbscript, file, mixed case, obfuscations).
4. Unconventional collection types and numeric anomalies in metrics_for (generators, numpy arrays, primitives, booleans).
5. Comprehensive mathematical correctness and invariants of Hirsch h-index.
"""

from __future__ import annotations

import html
from html.parser import HTMLParser
import re
from typing import Any, Dict, List
import numpy as np
import pandas as pd
import pytest

from app_pages import portfolio


# ──────────────────────────────────────────────────────────────────────────────
# HTML Security Parser for Genuine DOM-Level XSS Detection
# ──────────────────────────────────────────────────────────────────────────────
class XSSDOMAuditor(HTMLParser):
    """
    Parses generated HTML to verify that no dangerous tags or event handler
    attributes exist in the DOM structure (simulating browser tokenization).
    """
    DANGEROUS_TAGS = {"script", "img", "svg", "iframe", "object", "embed", "applet"}

    def __init__(self):
        super().__init__()
        self.found_dangerous_tags: List[str] = []
        self.found_event_handlers: List[tuple[str, str, str]] = []
        self.found_dangerous_urls: List[tuple[str, str, str]] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, str | None]]):
        tag_lower = tag.lower()
        if tag_lower in self.DANGEROUS_TAGS:
            self.found_dangerous_tags.append(tag_lower)

        for attr, val in attrs:
            attr_lower = attr.lower()
            val_str = str(val or "")
            # Check for inline event handler attributes (onclick, onerror, onload, etc.)
            if attr_lower.startswith("on"):
                self.found_event_handlers.append((tag, attr, val_str))
            # Check for executable pseudo-protocols in href or src
            if attr_lower in ("href", "src") and val_str:
                clean_val = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", val_str).strip().lower()
                if clean_val.startswith(("javascript:", "data:", "vbscript:")):
                    self.found_dangerous_urls.append((tag, attr, val_str))

    @classmethod
    def audit(cls, html_content: str) -> XSSDOMAuditor:
        auditor = cls()
        auditor.feed(html_content)
        return auditor


# ──────────────────────────────────────────────────────────────────────────────
# Reference Hirsch h-index Oracle for Property Verification
# ──────────────────────────────────────────────────────────────────────────────
def reference_h_index(citations: List[int]) -> int:
    """Independent canonical definition of Hirsch h-index."""
    clamped = [max(0, int(c)) for c in citations if not isinstance(c, bool)]
    sorted_c = sorted(clamped, reverse=True)
    h = 0
    for i, c in enumerate(sorted_c):
        if c >= i + 1:
            h = i + 1
        else:
            break
    return h


# ──────────────────────────────────────────────────────────────────────────────
# Suite 1: Regression Verification of the 6 Defect Fixes
# ──────────────────────────────────────────────────────────────────────────────
class TestDefectFixesRegression:
    """Verifies that all 6 defects reported by challenger_m1_1 are genuinely fixed."""

    def test_defect_1_xss_in_cited_by_fixed(self):
        """Confirm script payload in cited_by is escaped and does not execute."""
        df = [{"title": "Adversarial Paper", "cited_by": "<script>alert('xss')</script>"}]
        output = portfolio.to_html({}, df)
        assert "<script>alert('xss')</script>" not in output
        auditor = XSSDOMAuditor.audit(output)
        assert len(auditor.found_dangerous_tags) == 0

    def test_defect_2_empty_list_does_not_crash(self):
        """Confirm empty list does not raise AttributeError: 'list' object has no attribute 'empty'."""
        m = portfolio.metrics_for([])
        assert m["publications"] == 0
        assert m["citations"] == 0
        assert m["h_index"] == 0

        md = portfolio.to_markdown({}, [])
        assert "Total Publications:** 0" in md

        ht = portfolio.to_html({}, [])
        assert "No publications recorded yet." in ht

    def test_defect_3_non_string_profile_values_fixed(self):
        """Confirm non-string types in prof dict do not crash html.escape."""
        prof = {
            "name": 12345,
            "affiliation": 999,
            "tagline": True,
            "email": 42.0,
            "orcid": 1001,
            "website": 8888,
        }
        output = portfolio.to_html(prof, [])
        assert "12345" in output
        assert "999" in output

    def test_defect_4_ocr_enrich_none_and_empty(self):
        """Confirm ocr_enrich handles None, whitespace, and non-existent paths gracefully."""
        assert portfolio.ocr_enrich(None) == 0
        assert portfolio.ocr_enrich("") == 0
        assert portfolio.ocr_enrich("   ") == 0
        assert portfolio.ocr_enrich("non_existent_folder_xyz_123") == 0

    def test_defect_5_negative_citations_clamped(self):
        """Confirm negative citations are clamped to 0 and do not corrupt totals."""
        df = [
            {"title": "Paper A", "cited_by": -10},
            {"title": "Paper B", "cited_by": -5},
            {"title": "Paper C", "cited_by": 5},
        ]
        m = portfolio.metrics_for(df)
        assert m["citations"] == 5
        assert m["citations"] >= 0

    def test_defect_6_javascript_url_scheme_rejected(self):
        """Confirm javascript: URLs are not rendered as links in HTML."""
        prof = {"website": "javascript:alert('pwned')"}
        output = portfolio.to_html(prof, [])
        assert "javascript:alert" not in output
        auditor = XSSDOMAuditor.audit(output)
        assert len(auditor.found_dangerous_urls) == 0


# ──────────────────────────────────────────────────────────────────────────────
# Suite 2: Advanced XSS Payloads in cited_by & Profile Fields
# ──────────────────────────────────────────────────────────────────────────────
class TestAdversarialXSSBypasses:
    """Attempts evasion and filter bypass techniques on cited_by and profile fields."""

    ADVANCED_XSS_PAYLOADS = [
        "<<script>script>alert(1)<</script>/script>",
        "\" onclick=alert(1)>",
        "' onfocus=alert(1) autofocus='",
        "<img src=x onerror=alert(1)>",
        "<svg/onload=alert(1)>",
        "<iframe src=\"javascript:alert(1)\"></iframe>",
        "<body onload=alert(1)>",
        "<a href=\"javascript:alert(1)\">click me</a>",
        "';alert(String.fromCharCode(88,83,83))//",
        "<scr<script>ipt>alert(1)</script>",
        "<!--<script>alert(1)</script>-->",
        "<script \x00>alert(1)</script>",
        "<img src=\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' onload='alert(1)'/>\">",
    ]

    @pytest.mark.parametrize("payload", ADVANCED_XSS_PAYLOADS)
    def test_xss_in_cited_by_never_executes(self, payload: str):
        """Every advanced XSS payload in cited_by must be escaped into text, never parsed as DOM node."""
        df = [{"title": "Safe Title", "cited_by": payload}]
        out = portfolio.to_html({}, df)

        auditor = XSSDOMAuditor.audit(out)
        assert len(auditor.found_dangerous_tags) == 0, f"Dangerous DOM tag created by payload: {payload}"
        assert len(auditor.found_event_handlers) == 0, f"DOM Event handler created by payload: {payload}"
        assert len(auditor.found_dangerous_urls) == 0, f"Dangerous URL created by payload: {payload}"

    @pytest.mark.parametrize("payload", ADVANCED_XSS_PAYLOADS)
    def test_xss_in_profile_fields(self, payload: str):
        """Profile fields (name, affiliation, tagline, email, orcid) must not allow XSS injection."""
        prof = {
            "name": payload,
            "affiliation": payload,
            "tagline": payload,
            "email": payload,
            "orcid": payload,
        }
        out = portfolio.to_html(prof, [])

        auditor = XSSDOMAuditor.audit(out)
        assert len(auditor.found_dangerous_tags) == 0, f"Dangerous DOM tag created by profile field: {payload}"
        assert len(auditor.found_event_handlers) == 0, f"DOM Event handler created by profile field: {payload}"
        assert len(auditor.found_dangerous_urls) == 0, f"Dangerous URL created by profile field: {payload}"


# ──────────────────────────────────────────────────────────────────────────────
# Suite 3: Malicious URL Schemes in website Field
# ──────────────────────────────────────────────────────────────────────────────
class TestAdversarialURLSchemes:
    """Stress tests URL validation against malicious schemes and evasion tricks."""

    DANGEROUS_URLS = [
        # JavaScript schemes
        "javascript:alert(1)",
        "JavaScript:alert(1)",
        "JAVASCRIPT:alert(1)",
        "JaVaScRiPt:alert(1)",
        "javascript :alert(1)",
        "\tjavascript:alert(1)",
        "\njavascript:alert(1)",
        "\rjavascript:alert(1)",
        "javascript\x00:alert(1)",
        "javascript\x01:alert(1)",
        "javascript\x1f:alert(1)",
        # Data URLs
        "data:text/html,<script>alert(1)</script>",
        "DATA:text/html,<script>alert(1)</script>",
        "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
        "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxzY3JpcHQ+YWxlcnQoMSk8L3NjcmlwdD48L3N2Zz4=",
        # VBScript & Local files
        "vbscript:msgbox(1)",
        "VBSCRIPT:msgbox(1)",
        "file:///etc/passwd",
        "file:///C:/Windows/win.ini",
        "FILE:///C:/Windows/System32",
        # Other dangerous schemes
        "blob:http://evil.com/4e45d9fa-5d46-4c40-b484-9d047e17cb25",
        "about:blank",
        # Attribute breakout attempts
        "https://example.com' onclick=alert(1) '",
        "https://example.com\" onclick=alert(1) \"",
        "https://example.com' onmouseover='alert(1)",
    ]

    @pytest.mark.parametrize("bad_url", DANGEROUS_URLS)
    def test_sanitize_url_rejects_dangerous_schemes(self, bad_url: str):
        """_sanitize_url must neutralize all dangerous protocols and breakouts."""
        sanitized = portfolio._sanitize_url(bad_url)
        lower = sanitized.lower()
        assert not lower.startswith("javascript:"), f"Leaked javascript URL: {sanitized}"
        assert not lower.startswith("data:"), f"Leaked data URL: {sanitized}"
        assert not lower.startswith("vbscript:"), f"Leaked vbscript URL: {sanitized}"
        assert not lower.startswith("file:"), f"Leaked file URL: {sanitized}"
        assert not lower.startswith("blob:"), f"Leaked blob URL: {sanitized}"
        assert not lower.startswith("about:"), f"Leaked about URL: {sanitized}"

    @pytest.mark.parametrize("bad_url", DANGEROUS_URLS)
    def test_to_html_never_links_dangerous_url(self, bad_url: str):
        """to_html must never render an active link to a dangerous URL or attribute breakout."""
        prof = {"name": "Test User", "website": bad_url}
        out = portfolio.to_html(prof, [])

        auditor = XSSDOMAuditor.audit(out)
        assert len(auditor.found_dangerous_urls) == 0, f"Dangerous URL rendered in HTML: {auditor.found_dangerous_urls}"
        assert len(auditor.found_event_handlers) == 0, f"Event handler injected via URL attribute breakout: {auditor.found_event_handlers}"

    def test_safe_urls_preserved(self):
        """Verify standard academic URLs remain fully functional."""
        safe_urls = [
            ("https://lab.university.edu", "https://lab.university.edu"),
            ("http://researcher.org/~alice", "http://researcher.org/~alice"),
            ("www.researcher.org", "https://www.researcher.org"),
            ("scholar.google.com/citations?user=123", "https://scholar.google.com/citations?user=123"),
            ("mailto:prof@university.edu", "mailto:prof@university.edu"),
        ]
        for raw, expected in safe_urls:
            assert portfolio._sanitize_url(raw) == expected


# ──────────────────────────────────────────────────────────────────────────────
# Suite 4: Unconventional Collection Types & Boundary Primitives
# ──────────────────────────────────────────────────────────────────────────────
class TestAdversarialCollectionsAndTypes:
    """Stress tests _coerce_dataframe and metrics_for with unconventional types."""

    def test_generator_expression(self):
        """Passing a generator expression to metrics_for must not crash."""
        gen = ({"title": f"Paper {i}", "cited_by": i * 2} for i in range(5))
        res = portfolio.metrics_for(gen)
        assert isinstance(res, dict)
        assert "h_index" in res

    def test_empty_numpy_array(self):
        """Passing empty numpy array must return zero metrics without crash."""
        arr = np.array([])
        res = portfolio.metrics_for(arr)
        assert res["publications"] == 0
        assert res["citations"] == 0
        assert res["h_index"] == 0

    def test_numpy_2d_array(self):
        """Passing 2D numpy array must not crash."""
        arr = np.array([[1, 2], [3, 4]])
        res = portfolio.metrics_for(arr)
        assert isinstance(res, dict)

    def test_single_primitives(self):
        """Passing primitives (int, float, bool, str) must return zero metrics safely."""
        for val in [42, 3.14, True, False, "not a dataframe", b"bytes"]:
            res = portfolio.metrics_for(val)
            assert res["publications"] == 0
            assert res["citations"] == 0
            assert res["h_index"] == 0

    def test_dict_of_scalars(self):
        """Passing a single record dict directly must normalize to 1 publication."""
        data = {"title": "Single Paper", "cited_by": 10, "is_oa": True}
        res = portfolio.metrics_for(data)
        assert res["publications"] == 1
        assert res["citations"] == 10
        assert res["h_index"] == 1
        assert res["oa_share"] == 100.0

    def test_dict_of_lists(self):
        """Passing column-oriented dictionary must normalize cleanly."""
        data = {
            "title": ["Paper A", "Paper B", "Paper C"],
            "cited_by": [10, 20, 30],
            "journal": ["Nature", "Science", "Cell"],
        }
        res = portfolio.metrics_for(data)
        assert res["publications"] == 3
        assert res["citations"] == 60
        assert res["h_index"] == 3
        assert res["journals"] == 3

    def test_pandas_series_record(self):
        """Passing a pd.Series representing a publication record."""
        s = pd.Series({"title": "Series Paper", "cited_by": 5, "is_oa": False})
        res = portfolio.metrics_for(s)
        assert res["publications"] == 1
        assert res["citations"] == 5
        assert res["h_index"] == 1

    def test_citations_as_boolean_not_counted_as_one(self):
        """In Python, bool is a subclass of int (True == 1). Citations=True must NOT count as 1."""
        df = [
            {"title": "Paper True", "cited_by": True},
            {"title": "Paper False", "cited_by": False},
        ]
        res = portfolio.metrics_for(df)
        assert res["citations"] == 0
        assert res["h_index"] == 0

    def test_boundary_numerics_nan_and_scientific(self):
        """Verify handling of nan, none, string numbers, floats, and scientific notation."""
        df = [
            {"title": "Paper Normal", "cited_by": 10},
            {"title": "Paper NaN", "cited_by": float("nan")},
            {"title": "Paper None", "cited_by": None},
            {"title": "Paper String Number", "cited_by": "25"},
            {"title": "Paper Float String", "cited_by": "15.7"},
            {"title": "Paper Scientific", "cited_by": "1e2"},
        ]
        res = portfolio.metrics_for(df)
        assert res["publications"] == 6
        assert res["citations"] == 150
        assert res["h_index"] == 4


# ──────────────────────────────────────────────────────────────────────────────
# Suite 5: Hirsch h-index Mathematical Invariants & Property Tests
# ──────────────────────────────────────────────────────────────────────────────
class TestHirschIndexMathematicalInvariants:
    """Verifies that Hirsch h-index is 100% mathematically accurate against reference oracle."""

    @pytest.mark.parametrize("citations, expected_h", [
        ([], 0),
        ([0], 0),
        ([0, 0, 0, 0], 0),
        ([1], 1),
        ([100], 1),
        ([1, 1], 1),
        ([2, 2], 2),
        ([2, 1], 1),
        ([10, 8, 5, 4, 3], 4),
        ([25, 8, 5, 3, 3], 3),
        ([100, 0, 0, 0], 1),
        ([5, 5, 5, 5, 5], 5),
        ([6, 5, 5, 5, 5], 5),
        ([6, 6, 6, 6, 6, 6], 6),
        ([0, 100, 5, 2, 4, 3, 0], 3),
        (list(range(100)), 50),
    ])
    def test_canonical_h_index_values(self, citations: List[int], expected_h: int):
        df = [{"title": f"Paper {i}", "cited_by": c} for i, c in enumerate(citations)]
        res = portfolio.metrics_for(df)
        assert res["h_index"] == expected_h
        assert reference_h_index(citations) == expected_h

    def test_property_randomized_citation_distributions(self):
        """Property test: for 500 randomized citation distributions, h_index matches oracle."""
        rng = np.random.default_rng(42)
        for _ in range(500):
            n_pubs = int(rng.integers(0, 50))
            if n_pubs == 0:
                cites = []
            else:
                cites = [int(x) for x in rng.integers(0, 100, size=n_pubs)]

            df = [{"title": f"Paper {i}", "cited_by": c} for i, c in enumerate(cites)]
            m = portfolio.metrics_for(df)
            expected = reference_h_index(cites)

            # Mathematical Invariant 1: Matches reference oracle exactly
            assert m["h_index"] == expected, f"Failed for cites: {cites}"
            # Mathematical Invariant 2: 0 <= h <= n_pubs
            assert 0 <= m["h_index"] <= n_pubs
            # Mathematical Invariant 3: if cites, h <= max(cites)
            if cites:
                assert m["h_index"] <= max(cites)
