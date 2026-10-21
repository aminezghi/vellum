"""Unit tests for citation_core module."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from citation_core import (
    clean_doi,
    _parse_openalex_work,
    resolve_seed,
    build_citation_network,
)


class TestCitationCore(unittest.TestCase):
    def test_clean_doi_standard(self):
        self.assertEqual(clean_doi("10.1038/s41598-024-73169-2"), "10.1038/s41598-024-73169-2")

    def test_clean_doi_with_url_prefix(self):
        self.assertEqual(
            clean_doi("https://doi.org/10.1016/j.ajcn.2002.12.001"),
            "10.1016/j.ajcn.2002.12.001"
        )
        self.assertEqual(
            clean_doi("http://dx.doi.org/10.1145/1234567.1234568"),
            "10.1145/1234567.1234568"
        )

    def test_clean_doi_trailing_punctuation(self):
        self.assertEqual(clean_doi("10.1000/182."), "10.1000/182")
        self.assertEqual(clean_doi(" 10.1000/182; "), "10.1000/182")

    def test_parse_openalex_work_inverted_abstract(self):
        payload = {
            "id": "https://openalex.org/W999999",
            "doi": "https://doi.org/10.1000/example",
            "title": "A Breakthrough Study in Machine Learning",
            "publication_year": 2023,
            "cited_by_count": 42,
            "authorships": [
                {"author": {"display_name": "Alice Smith"}},
                {"author": {"display_name": "Bob Jones"}},
            ],
            "primary_location": {
                "source": {"display_name": "Journal of AI"},
                "pdf_url": "https://example.com/paper.pdf",
            },
            "abstract_inverted_index": {
                "Machine": [0],
                "learning": [1],
                "advances": [2],
                "rapidly": [3],
            },
            "referenced_works": ["https://openalex.org/W111", "https://openalex.org/W222"],
            "open_access": {"is_oa": True},
        }

        parsed = _parse_openalex_work(payload)
        self.assertEqual(parsed["openalex_id"], "W999999")
        self.assertEqual(parsed["doi"], "10.1000/example")
        self.assertEqual(parsed["title"], "A Breakthrough Study in Machine Learning")
        self.assertEqual(parsed["year"], 2023)
        self.assertEqual(parsed["cited_by_count"], 42)
        self.assertEqual(parsed["authors"], ["Alice Smith", "Bob Jones"])
        self.assertEqual(parsed["venue"], "Journal of AI")
        self.assertEqual(parsed["pdf_url"], "https://example.com/paper.pdf")
        self.assertEqual(parsed["abstract"], "Machine learning advances rapidly")
        self.assertTrue(parsed["is_oa"])

    def test_resolve_seed_with_mock_session(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "https://openalex.org/W12345",
            "doi": "https://doi.org/10.1000/mock",
            "title": "Mock Seed Paper",
            "publication_year": 2021,
            "authorships": [{"author": {"display_name": "Dr. Example"}}],
        }
        mock_session.get.return_value = mock_resp

        result = resolve_seed("10.1000/mock", session=mock_session)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Mock Seed Paper")
        self.assertEqual(result["doi"], "10.1000/mock")

    def test_build_citation_network_structure(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {
                    "id": "https://openalex.org/W2001",
                    "doi": "https://doi.org/10.1000/ref1",
                    "title": "Prior Foundation Work",
                    "publication_year": 2010,
                    "cited_by_count": 500,
                    "authorships": [{"author": {"display_name": "Foundational Author"}}],
                }
            ]
        }
        mock_session.get.return_value = mock_resp

        seed = {
            "id": "W1000",
            "openalex_id": "W1000",
            "title": "Central Paper",
            "year": 2020,
            "authors": ["Lead Researcher"],
            "venue": "Nature",
            "cited_by_count": 100,
            "doi": "10.1000/seed",
            "pdf_url": "https://nature.com/seed.pdf",
            "referenced_works": ["https://openalex.org/W2001"],
        }

        network = build_citation_network(seed, session=mock_session)
        self.assertIn("nodes", network)
        self.assertIn("links", network)
        self.assertEqual(network["seed_id"], "W1000")
        self.assertGreaterEqual(len(network["nodes"]), 1)
        # Check node schema
        seed_node = next(n for n in network["nodes"] if n["id"] == "W1000")
        self.assertEqual(seed_node["type"], "seed")
        self.assertEqual(seed_node["title"], "Central Paper")


if __name__ == "__main__":
    unittest.main()
