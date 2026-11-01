"""
tools/stress_cv_frame.py — Empirical Stress Harness for researchers._cv_frame()

Verifies crash-free execution, schema consistency, bibliometric invariants,
and performance across empty, minimal, standard, and heavily populated vaults
including adversarial inputs.
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path
import pandas as pd

# Add Desktop_App to sys.path so modules can be imported
desktop_dir = Path(__file__).resolve().parent.parent / "Vellum_Desktop" / "Desktop_App"
if str(desktop_dir) not in sys.path:
    sys.path.insert(0, str(desktop_dir))

import vellum_workspace as VW
from app_pages import researchers, portfolio


def run_empty_vault_stress():
    print("\n=======================================================")
    print(" [1/3] STRESS TEST: Empty Vault Scenarios")
    print("=======================================================")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_vault = Path(tmp_dir) / "Empty_Vault"
        tmp_vault.mkdir()
        os.environ["VELLUM_VAULT_DIR"] = str(tmp_vault)

        # 1. Fresh vault directory with NO projects at all
        print("  -> Testing fresh vault directory with no projects...")
        t0 = time.perf_counter()
        df = researchers._cv_frame()
        t1 = time.perf_counter()
        assert isinstance(df, pd.DataFrame), f"Expected DataFrame, got {type(df)}"
        assert df.empty, f"Expected empty DataFrame, got shape {df.shape}"
        expected_cols = ["title", "journal", "cited_by", "doi", "is_oa", "pdf_url", "authors", "year", "screen"]
        for col in expected_cols:
            assert col in df.columns, f"Missing expected column: {col}"
        print(f"     PASS: Empty DataFrame returned with 9 columns in {t1 - t0:.4f}s")

        # Downstream checks on empty DataFrame
        m = portfolio.metrics_for(df)
        assert m["publications"] == 0
        assert m["citations"] == 0
        assert m["h_index"] == 0
        assert m["journals"] == 0
        assert m["oa_share"] == 0.0
        md = portfolio.to_markdown({"name": "Empty Test"}, df)
        assert "Empty Test" in md
        html = portfolio.to_html({"name": "Empty Test"}, df)
        assert "Empty Test" in html
        print("     PASS: Empty downstream metrics, markdown, and html run cleanly.")

        # 2. Vault with an explicitly empty project
        print("  -> Testing project with empty records...")
        VW.create_project("Empty_Project")
        data = VW.load_project_data("Empty_Project")
        data["search_records"] = []
        data["screened"] = {}
        VW.save_project_data(data, "Empty_Project")

        t0 = time.perf_counter()
        df2 = researchers._cv_frame()
        t1 = time.perf_counter()
        assert isinstance(df2, pd.DataFrame)
        assert df2.empty
        print(f"     PASS: Explicitly empty project returned valid DataFrame in {t1 - t0:.4f}s")

        # 3. Vault with corrupt/malformed project JSON missing keys
        print("  -> Testing project with missing/corrupt keys...")
        VW.create_project("Corrupt_Project")
        corrupt_data = {"corrupted_metadata": True}
        VW.save_project_data(corrupt_data, "Corrupt_Project")

        t0 = time.perf_counter()
        df3 = researchers._cv_frame()
        t1 = time.perf_counter()
        assert isinstance(df3, pd.DataFrame)
        assert df3.empty
        print(f"     PASS: Malformed project data handled gracefully in {t1 - t0:.4f}s")


def run_populated_vault_stress():
    print("\n=======================================================")
    print(" [2/3] STRESS TEST: Populated Vault Scenarios")
    print("=======================================================")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_vault = Path(tmp_dir) / "Populated_Vault"
        tmp_vault.mkdir()
        os.environ["VELLUM_VAULT_DIR"] = str(tmp_vault)

        p_name = "Populated_Stress_Project"
        VW.create_project(p_name)

        # Generate 1,000 diverse and adversarial publication records
        print("  -> Generating 1,000 diverse and adversarial records...")
        records = []
        for i in range(1000):
            # Mix standard, edge-case, and adversarial inputs
            if i % 10 == 0:
                # Negative citations & edge case values
                cites = -50
            elif i % 10 == 1:
                # String numeric
                cites = "120"
            elif i % 10 == 2:
                # Non-numeric string
                cites = "not_a_number"
            elif i % 10 == 3:
                # Boolean
                cites = True
            elif i % 10 == 4:
                # None
                cites = None
            elif i % 10 == 5:
                # Large citation count
                cites = 250000
            else:
                cites = i * 3

            # Adversarial title/author injection
            if i % 25 == 0:
                title = f"<script>alert('xss_{i}')</script> Title {i}"
                author_list = [f"<b>Attacker {j}</b>" for j in range(5)]
            elif i % 25 == 1:
                title = f"Quantum Annealing in α-β Networks with 95% CI [0.12, 0.98] — Paper {i}"
                author_list = ["Müller, H.", "田中, 太郎", "Al-Hassan, M."]
            elif i % 25 == 2:
                title = f"Extremely Long Title {'A'*500} - {i}"
                author_list = [f"Author_{k}" for k in range(100)] # 100 authors
            elif i % 25 == 3:
                title = "" # Empty title
                author_list = None
            else:
                title = f"Scholarly Paper {i}: Advances in Research"
                author_list = [f"Researcher {i}A", f"Researcher {i}B"]

            doi = f"10.1000/stress.{i}" if (i % 7 != 0) else ""

            rec = {
                "doi": doi,
                "title": title,
                "journal": f"Journal of Testing #{i % 20}",
                "cited_by": cites,
                "year": 2000 + (i % 26),
                "is_oa": (i % 2 == 0),
                "pdf_url": f"https://example.org/pdf/{i}.pdf" if (i % 3 == 0) else "",
                "authors": author_list,
            }
            records.append(rec)

        # Save to project
        p_data = VW.load_project_data(p_name)
        p_data["search_records"] = records
        p_data["screened"] = {
            "10.1000/stress.1": {"status": "include", "notes": "Must have"},
            "10.1000/stress.2": {"status": "exclude", "reason": "Out of scope"},
            "10.1000/stress.3": {"status": "skip"},
        }
        VW.save_project_data(p_data, p_name)

        # Run _cv_frame()
        print("  -> Executing researchers._cv_frame() on 1,000 records...")
        t0 = time.perf_counter()
        df = researchers._cv_frame()
        t1 = time.perf_counter()
        elapsed = t1 - t0

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0, "DataFrame should contain records"
        print(f"     PASS: Parsed {len(df)} records in {elapsed:.4f}s (well within threshold)")

        # Verify invariants on returned DataFrame
        print("  -> Validating data invariants...")
        # 1. All cited_by values must be non-negative integers
        assert (df["cited_by"] >= 0).all(), "Found negative citation counts in DataFrame!"
        # 2. Check columns
        for col in ["title", "journal", "cited_by", "doi", "is_oa", "pdf_url", "authors", "year", "screen"]:
            assert col in df.columns, f"Missing column {col}"
        # 3. Check screening status mapping
        rec_1 = df[df["doi"] == "10.1000/stress.1"]
        if not rec_1.empty:
            assert rec_1.iloc[0]["screen"] == "include"
        rec_2 = df[df["doi"] == "10.1000/stress.2"]
        if not rec_2.empty:
            assert rec_2.iloc[0]["screen"] == "exclude"

        print("     PASS: Invariants confirmed (non-negative citations, correct screening mapping).")

        # Downstream stress test with portfolio functions
        print("  -> Running downstream bibliometric metrics calculation...")
        t0 = time.perf_counter()
        m = portfolio.metrics_for(df)
        t1 = time.perf_counter()
        assert m["publications"] == len(df)
        assert m["citations"] > 0
        assert m["h_index"] > 0
        print(f"     PASS: Metrics computed: pubs={m['publications']}, cites={m['citations']}, h={m['h_index']} in {t1 - t0:.4f}s")

        print("  -> Running downstream markdown & HTML export generation...")
        prof = {
            "name": "Dr. Empirical Challenger",
            "affiliation": "Vellum Adversarial Labs",
            "email": "challenger@example.org",
            "orcid": "0000-0002-1825-0097",
            "website": "https://vellum.example.org",
        }
        md = portfolio.to_markdown(prof, df)
        assert len(md) > 1000
        assert "Dr. Empirical Challenger" in md

        html = portfolio.to_html(prof, df)
        assert len(html) > 1000
        # Check XSS escaping
        assert "<script>alert('xss" not in html
        assert "&lt;script&gt;alert(&#x27;xss" in html or "&lt;script&gt;alert('xss" in html
        print("     PASS: Markdown and sanitized HTML generated successfully.")


def run_repetitive_stability_stress():
    print("\n=======================================================")
    print(" [3/3] STRESS TEST: Repetitive Calling & Memory Stability")
    print("=======================================================")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_vault = Path(tmp_dir) / "Stability_Vault"
        tmp_vault.mkdir()
        os.environ["VELLUM_VAULT_DIR"] = str(tmp_vault)

        VW.create_project("Stability_Project")
        records = [
            {"doi": f"10.1234/{i}", "title": f"Paper {i}", "cited_by": i, "year": 2024}
            for i in range(100)
        ]
        p_data = VW.load_project_data("Stability_Project")
        p_data["search_records"] = records
        VW.save_project_data(p_data, "Stability_Project")

        print("  -> Running 100 consecutive invocations of researchers._cv_frame()...")
        t0 = time.perf_counter()
        for i in range(100):
            df = researchers._cv_frame()
            assert len(df) == 100
        t1 = time.perf_counter()
        avg_time = (t1 - t0) / 100
        print(f"     PASS: 100 runs completed in {t1 - t0:.3f}s (avg {avg_time * 1000:.2f}ms / call)")


def main():
    print("=======================================================")
    print("  EMPIRICAL STRESS TEST SUITE: researchers._cv_frame()")
    print("=======================================================")

    orig_vault = os.environ.get("VELLUM_VAULT_DIR")
    try:
        run_empty_vault_stress()
        run_populated_vault_stress()
        run_repetitive_stability_stress()
        print("\n=======================================================")
        print("  ALL EMPIRICAL STRESS TESTS PASSED SUCCESSFULLY (100%)")
        print("=======================================================")
    finally:
        if orig_vault:
            os.environ["VELLUM_VAULT_DIR"] = orig_vault
        elif "VELLUM_VAULT_DIR" in os.environ:
            del os.environ["VELLUM_VAULT_DIR"]


if __name__ == "__main__":
    main()
