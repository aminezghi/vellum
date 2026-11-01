"""Cross-app exchange check: Vellum Desktop exports -> Vellum Web import.

The desktop exporter (``vellum_citation_export``) writes RIS and BibTeX; the web
studio's importer (``parseUniversalFile`` in ``src/lib/activeLearning.ts``)
reads them. This test runs the real code on both sides, so a format change in
either app that breaks the hand-off fails here.

    Vellum_Desktop/Desktop_App/.venv/Scripts/python.exe -m pytest tools/test_cross_app_exchange.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DESKTOP_APP = REPO_ROOT / "Vellum_Desktop" / "Desktop_App"
WEB_APP = REPO_ROOT / "Vellum_Web" / "Web_App_Fernly"
PARSE_CLI = WEB_APP / "tests" / "parseFileCli.mjs"

sys.path.insert(0, str(DESKTOP_APP))
from vellum_citation_export import export_to_bibtex, export_to_ris  # noqa: E402

NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(
    NODE is None or not (WEB_APP / "node_modules" / "jiti").exists(),
    reason="node and the web app's node_modules are needed to run the web importer",
)

PAPERS = [
    {
        "title": "Deep learning for fruit detection in orchards",
        "authors": ["Sa, Inkyu", "Ge, Zongyuan", "Dayoub, Feras"],
        "year": 2016,
        "journal": "Sensors",
        "doi": "10.3390/s16081222",
        "abstract": "We present a novel approach to fruit detection using deep convolutional networks.",
    },
    {
        "title": "Évaluation des politiques de santé publique : une revue",
        "authors": ["Müller, Jürgen", "Ødegaard, Siv"],
        "year": "2021",
        "venue": "Revue d'Épidémiologie",
        "doi": "10.1016/j.respe.2021.01.002",
        "abstract": "First line of the abstract.\nSecond line continues the same abstract.",
    },
    {
        "title": "A single-author paper with a DOI URL",
        "authors": "Doe, Jane",
        "year": 2019,
        "journal": "Journal of Testing",
        "doi": "10.1000/xyz123",
    },
]


def _parse_with_web(tmp_path: Path, name: str, text: str) -> list[dict]:
    target = tmp_path / name
    target.write_text(text, encoding="utf-8")
    proc = subprocess.run(
        [NODE, str(PARSE_CLI), str(target)],
        cwd=WEB_APP,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    assert proc.returncode == 0, f"web importer crashed:\n{proc.stderr}"
    return json.loads(proc.stdout)


def _by_title(records: list[dict]) -> dict[str, dict]:
    return {r["title"]: r for r in records}


@pytest.mark.parametrize(
    "exporter,filename",
    [(export_to_ris, "desktop_export.ris"), (export_to_bibtex, "desktop_export.bib")],
)
def test_every_desktop_record_imports_into_web(tmp_path, exporter, filename):
    records = _parse_with_web(tmp_path, filename, exporter(PAPERS))
    assert len(records) == len(PAPERS)
    got = _by_title(records)
    for paper in PAPERS:
        rec = got.get(paper["title"])
        assert rec is not None, f"title lost in transit: {paper['title']!r}; got {list(got)}"
        assert rec["doi"] == paper["doi"]
        assert rec["year"] == int(paper["year"])
        assert rec["decision"] == "pending"


@pytest.mark.parametrize(
    "exporter,filename",
    [(export_to_ris, "desktop_export.ris"), (export_to_bibtex, "desktop_export.bib")],
)
def test_authors_and_venue_survive(tmp_path, exporter, filename):
    got = _by_title(_parse_with_web(tmp_path, filename, exporter(PAPERS)))
    for paper in PAPERS:
        rec = got[paper["title"]]
        expected_authors = paper["authors"] if isinstance(paper["authors"], list) else [paper["authors"]]
        assert rec["authors"] == expected_authors
        assert rec["journal"] == (paper.get("journal") or paper.get("venue"))


def test_ris_abstract_survives_including_multiline(tmp_path):
    got = _by_title(_parse_with_web(tmp_path, "desktop_export.ris", export_to_ris(PAPERS)))
    first = got[PAPERS[0]["title"]]
    assert first["abstract"] == PAPERS[0]["abstract"]
    multiline = got[PAPERS[1]["title"]]
    assert "First line of the abstract." in multiline["abstract"]
    assert "Second line continues the same abstract." in multiline["abstract"]


def test_empty_desktop_export_imports_as_nothing(tmp_path):
    assert _parse_with_web(tmp_path, "empty.ris", export_to_ris([])) == []
