"""Unit tests for litcheck_core normalisation and deduplication logic."""

from __future__ import annotations

import unittest

from litcheck_core import (
    norm_title,
    title_tokens,
    sim_title,
    fingerprint,
    author_key,
    _title_merge_allowed,
    deduplicate,
)


class TestLitcheckCore(unittest.TestCase):
    def test_norm_title_strips_punctuation_and_casing(self):
        raw = "  Deep Learning in Health: A Systematic Review & Meta-Analysis!  "
        expected = "deep learning in health a systematic review meta analysis"
        self.assertEqual(norm_title(raw), expected)

    def test_norm_title_handles_accents_and_html(self):
        raw = "<i>Étude préliminaire</i> sur l'efficacité"
        expected = "etude preliminaire sur l efficacite"
        self.assertEqual(norm_title(raw), expected)

    def test_norm_title_empty_or_none(self):
        self.assertEqual(norm_title(None), "")
        self.assertEqual(norm_title(""), "")

    def test_sim_title_identical(self):
        self.assertEqual(sim_title("Machine Learning in Radiology", "Machine Learning in Radiology"), 1.0)

    def test_sim_title_different(self):
        score = sim_title("Quantum Computing", "Deep Neural Networks")
        self.assertLess(score, 0.4)

    def test_author_key_normalization(self):
        self.assertEqual(author_key("John D. Smith"), author_key("John D Smith"))

    def test_title_merge_allowed_prevents_conflicting_dois(self):
        # Two records with same title but different registered DOIs must NOT merge
        r1 = {"title": "Clinical Trial Results", "doi": "10.1000/trial1", "year": 2021}
        r2 = {"title": "Clinical Trial Results", "doi": "10.1000/trial2", "year": 2021}
        self.assertFalse(_title_merge_allowed(r1, r2, slack=1))

    def test_title_merge_allowed_accepts_compatible_years_and_missing_doi(self):
        # Record with no DOI should merge with one that has a DOI if title & year match
        r1 = {"title": "Clinical Trial Results", "doi": "10.1000/trial1", "year": 2021}
        r2 = {"title": "Clinical Trial Results", "doi": "", "year": 2021}
        self.assertTrue(_title_merge_allowed(r1, r2, slack=1))

    def test_deduplicate_exact_doi(self):
        records = [
            {
                "title": "Paper Alpha",
                "doi": "10.1234/alpha",
                "year": 2020,
                "authors": ["Smith J"],
                "source": "openalex",
            },
            {
                "title": "Paper Alpha (Crossref)",
                "doi": "10.1234/alpha",
                "year": 2020,
                "authors": ["Smith John"],
                "source": "crossref",
            },
        ]
        unique_records, audit_rows, conflicts = deduplicate(records)
        self.assertEqual(len(unique_records), 1)
        self.assertIn("openalex", unique_records[0]["sources"])
        self.assertIn("crossref", unique_records[0]["sources"])
        self.assertEqual(unique_records[0]["source_count"], 2)


if __name__ == "__main__":
    unittest.main()
