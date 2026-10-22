"""
tests/test_screening_engine.py — Unit test suite for ASReview Active Learning Screening Engine.
"""

import sys
from pathlib import Path

# Ensure Desktop_App is on sys.path
desktop_dir = Path(__file__).resolve().parent.parent
if str(desktop_dir) not in sys.path:
    sys.path.insert(0, str(desktop_dir))

import pytest
from app_pages.screening import (
    normalize_doi,
    normalize_title,
    get_word_tokens,
    token_jaccard_similarity,
    deduplicate_records,
    parse_ris_text,
    parse_bibtex_text,
    ASReviewActiveLearningModel,
    SKLEARN_AVAILABLE,
)


def test_normalize_doi():
    assert normalize_doi("https://doi.org/10.1038/s41586-020-2649-2") == "10.1038/s41586-020-2649-2"
    assert normalize_doi("doi: 10.1038/s41586-020-2649-2 ") == "10.1038/s41586-020-2649-2"
    assert normalize_doi("HTTP://DX.DOI.ORG/10.1109/CVPR.2016.90") == "10.1109/cvpr.2016.90"
    assert normalize_doi(None) == ""


def test_normalize_title():
    t1 = "DeepFruits: A Fruit Detection System Using Deep Neural Networks"
    t2 = "deepfruits a fruit detection system using deep neural networks"
    assert normalize_title(t1) == normalize_title(t2)

    t3 = "The Impact of Transformers on Natural Language Processing"
    t4 = "Impact of Transformers on Natural Language Processing"
    assert normalize_title(t3) == normalize_title(t4)


def test_token_jaccard_similarity():
    s1 = get_word_tokens("Deep learning for fruit detection in orchards")
    s2 = get_word_tokens("Deep learning for apple detection in orchards")
    sim = token_jaccard_similarity(s1, s2)
    assert sim > 0.60
    assert token_jaccard_similarity(set(), s2) == 0.0


def test_deduplicate_records_doi():
    existing = [
        {"id": "p1", "title": "AlphaFold Protein Structure", "doi": "10.1038/s41586-021-03819-2", "decision": "pending"}
    ]
    new_items = [
        {"title": "Highly Accurate Protein Structure Prediction with AlphaFold", "doi": "https://doi.org/10.1038/s41586-021-03819-2", "abstract": "New abstract"}
    ]
    combined, dup_count, details = deduplicate_records(existing, new_items, "Crossref Import")
    assert dup_count == 1
    assert len(combined) == 1
    assert details[0]["reason"] == "Exact DOI Match"
    assert combined[0]["abstract"] == "New abstract"


def test_deduplicate_records_fuzzy_title():
    existing = [
        {"id": "p1", "title": "DeepFruits: A Fruit Detection System Using Deep Neural Networks", "decision": "pending"}
    ]
    new_items = [
        {"title": "DeepFruits: A Fruit Detection System Using Deep Neural Networks", "journal": "Sensors"}
    ]
    combined, dup_count, details = deduplicate_records(existing, new_items, "Scopus Import")
    assert dup_count == 1
    assert len(combined) == 1


def test_parse_ris_text():
    sample_ris = """
TY  - JOUR
TI  - Attention Is All You Need
AU  - Vaswani, Ashish
AU  - Shazeer, Noam
PY  - 2017
JO  - NeurIPS
DO  - 10.48550/arXiv.1706.03762
AB  - The dominant sequence transduction models are based on complex recurrent...
ER  - 
"""
    records = parse_ris_text(sample_ris)
    assert len(records) == 1
    assert records[0]["title"] == "Attention Is All You Need"
    assert len(records[0]["authors"]) == 2
    assert records[0]["year"] == 2017
    assert records[0]["doi"] == "10.48550/arXiv.1706.03762"


def test_parse_bibtex_text():
    sample_bib = """
@article{vaswani2017attention,
  title = {Attention Is All You Need},
  author = {Vaswani, Ashish and Shazeer, Noam},
  year = {2017},
  journal = {Advances in Neural Information Processing Systems},
  doi = {10.48550/arXiv.1706.03762},
  abstract = {The dominant sequence transduction models are based on complex recurrent...}
}
"""
    records = parse_bibtex_text(sample_bib)
    assert len(records) == 1
    assert records[0]["title"] == "Attention Is All You Need"
    assert records[0]["year"] == 2017


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn required for active learning test")
def test_active_learning_rerank():
    candidates = [
        {
            "id": "c1",
            "title": "DeepFruits: A Fruit Detection System Using Deep Neural Networks",
            "abstract": "Fruit detection in agriculture using convolutional neural networks and faster rcnn",
            "decision": "included",
        },
        {
            "id": "c2",
            "title": "Soil chemistry and organic matter decomposition in temperate forests",
            "abstract": "Analysis of mineral soil horizons and humus chemistry under seasonal rainfall",
            "decision": "excluded",
        },
        {
            "id": "c3",
            "title": "Computer vision and fruit harvesting robotics",
            "abstract": "Autonomous apple and fruit picking using deep neural networks and orchard vision",
            "decision": "pending",
        },
        {
            "id": "c4",
            "title": "Mineral extraction and chemical metallurgy",
            "abstract": "Thermodynamics of nickel and iron leaching in acidic aqueous solvents",
            "decision": "pending",
        },
    ]

    model = ASReviewActiveLearningModel()
    reranked = model.fit_and_rerank(candidates)
    
    pending_ranked = [c for c in reranked if c.get("decision") == "pending"]
    assert len(pending_ranked) == 2
    # c3 (fruit harvesting robotics) should be ranked higher than c4 (mineral extraction)
    assert pending_ranked[0]["id"] == "c3"
    assert pending_ranked[0]["relevance_score"] > pending_ranked[1]["relevance_score"]
