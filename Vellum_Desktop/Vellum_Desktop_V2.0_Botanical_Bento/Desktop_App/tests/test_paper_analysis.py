"""Unit tests for paper_analysis evidence-linked appraisal engine."""

from __future__ import annotations

import unittest

from paper_analysis import (
    DATA_MODALITY,
    scan_lexicon,
    _compile,
    count_in,
    _P_RE,
    _CI_RE,
)


class TestPaperAnalysis(unittest.TestCase):
    def test_scan_lexicon_data_modality_survey(self):
        compiled = _compile(DATA_MODALITY)
        sample_pages = [
            "We administered a 42-item questionnaire to participants across three hospitals."
        ]
        hits = scan_lexicon(sample_pages, compiled)
        labels = [h["label"] for h in hits]
        self.assertIn("Questionnaire / survey", labels)

    def test_scan_lexicon_data_modality_neuroimaging(self):
        compiled = _compile(DATA_MODALITY)
        sample_pages = [
            "Whole-brain functional magnetic resonance imaging was conducted on a 3T scanner with fMRI sequences."
        ]
        hits = scan_lexicon(sample_pages, compiled)
        labels = [h["label"] for h in hits]
        self.assertIn("Neuroimaging", labels)

    def test_p_value_counting(self):
        text = "The effect was significant at p < .001 and also observed at p = 0.042, whereas control showed p > 0.10."
        count = count_in(text, _P_RE)
        self.assertEqual(count, 3)

    def test_ci_regex(self):
        text = "The hazard ratio was 0.72 (95% CI 0.58-0.89) and odds ratio was 1.45 (95% confidence interval: 1.12 to 1.88)."
        hits = _CI_RE.findall(text)
        self.assertGreaterEqual(len(hits), 1)


if __name__ == "__main__":
    unittest.main()
