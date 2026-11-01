"""
test_vellum_workflow.py — Tests for the frosted theme, unified paper pool, and project overview.
"""

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

BASE_DIR = Path(__file__).resolve().parent.parent

import vellum_theme as VT
import vellum_paper_pool as VPP
import vellum_workspace as VW
import vellum_paths as VP


class TestVellumWorkflow(unittest.TestCase):
    def test_frosted_theme_css_contains_core_classes(self):
        css = VT.FROSTED_GLASS_CSS
        self.assertIn(".glass-panel", css)
        self.assertIn(".glass-metric", css)
        self.assertIn(".badge-emerald", css)
        self.assertIn(".badge-sky", css)
        self.assertIn("backdrop-filter", css)

    def test_paper_pool_module_available(self):
        self.assertTrue(callable(VPP.render_paper_card))
        self.assertTrue(callable(VPP.render_paper_pool))

    @patch("streamlit.markdown")
    def test_inject_theme_calls_markdown(self, mock_markdown):
        VT.inject_theme()
        mock_markdown.assert_called_once()
        args, kwargs = mock_markdown.call_args
        self.assertIn("<style>", args[0])
        self.assertTrue(kwargs.get("unsafe_allow_html"))

    def test_citation_exports(self):
        import vellum_citation_export as VCE
        sample_papers = [{
            "title": "Machine Learning in Systematic Reviews",
            "authors": ["Amine Zouaghi", "Co Author"],
            "year": 2026,
            "doi": "10.1000/182",
            "journal": "Journal of Research Synthesis",
            "abstract": "This study analyzes automated literature screening.",
        }]
        # Test Zotero RIS export
        ris = VCE.export_to_ris(sample_papers)
        self.assertIn("TY  - JOUR", ris)
        self.assertIn("TI  - Machine Learning in Systematic Reviews", ris)
        self.assertIn("AU  - Amine Zouaghi", ris)
        self.assertIn("DO  - 10.1000/182", ris)
        self.assertIn("ER  -", ris)

        # Test EndNote ENW export
        enw = VCE.export_to_endnote_enw(sample_papers)
        self.assertIn("%0 Journal Article", enw)
        self.assertIn("%T Machine Learning in Systematic Reviews", enw)
        self.assertIn("%A Amine Zouaghi", enw)
        self.assertIn("%R 10.1000/182", enw)

        # Test BibTeX export
        bib = VCE.export_to_bibtex(sample_papers)
        self.assertIn("@article{", bib)
        self.assertIn("Machine Learning in Systematic Reviews", bib)

    def test_direct_download_queue(self):
        import vellum_direct_download as VDD
        p_name = "Workflow_Queue_Test"
        VW.create_project(p_name)
        VDD.clear_download_queue(p_name)
        self.assertEqual(len(VDD.get_download_queue(p_name)), 0)

        paper = {"title": "Test Queue Paper", "doi": "10.1000/queue1", "year": 2026}
        added = VDD.add_to_download_queue(paper, p_name)
        self.assertTrue(added)
        q = VDD.get_download_queue(p_name)
        self.assertEqual(len(q), 1)
        self.assertEqual(q[0]["title"], "Test Queue Paper")

        # Duplicate should be rejected
        added_again = VDD.add_to_download_queue(paper, p_name)
        self.assertFalse(added_again)

        VDD.clear_download_queue(p_name)
        self.assertEqual(len(VDD.get_download_queue(p_name)), 0)

    def test_clean_html_removes_newlines_and_indents(self):
        from app_pages.project_overview import _clean_html
        raw = """
        <div class="card">
            <p>   Indented content   </p>
        </div>
        """
        cleaned = _clean_html(raw)
        self.assertNotIn("\n", cleaned)
        self.assertEqual(cleaned, '<div class="card"> <p>   Indented content   </p> </div>')

    def test_save_citation_export(self):
        import vellum_citation_export as VCE
        p_name = "Export_Save_Test"
        VW.create_project(p_name)
        vp, dp = VCE.save_citation_export("test.ris", "TY  - JOUR\nER  -", p_name)
        self.assertTrue(vp.exists())
        self.assertEqual(vp.read_text(encoding="utf-8"), "TY  - JOUR\nER  -")
        if dp:
            self.assertTrue(dp.exists())

    def test_dark_light_theme_toggle_and_css(self):
        VT.set_theme_mode("dark")
        self.assertTrue(VT.is_dark_mode())
        dark_css = VT.get_theme_css(dark=True)
        self.assertIn("#1a1a1a", dark_css)
        self.assertIn("#0a84ff", dark_css)
        self.assertIn("button[data-selected]", dark_css)

        VT.toggle_theme_mode()
        self.assertFalse(VT.is_dark_mode())
        light_css = VT.get_theme_css(dark=False)
        self.assertIn("#007aff", light_css)
        self.assertIn("button[data-selected]", light_css)

        # Restore dark
        VT.set_theme_mode("dark")
        self.assertTrue(VT.is_dark_mode())

    def test_citation_graph_litmaps_light_styling(self):
        import app_pages.citation_graph as CG
        dummy_graph = {"nodes": [], "links": [], "stats": {}}
        with patch("streamlit.components.v1.html") as mock_html:
            CG._render_d3_graph(dummy_graph, dark=False)
            mock_html.assert_called_once()
            html_call = mock_html.call_args[0][0]
            self.assertIn("#ffffff", html_call)
            self.assertIn("#2563eb", html_call)
            self.assertIn("#1e293b", html_call)

    def test_user_profile_theme_setting(self):
        prof = VW.get_user_profile()
        VW.set_user_profile(
            name=prof.get("name", "Test"),
            field=prof.get("field", "AI"),
            keywords=prof.get("keywords", "ml"),
            theme="light",
        )
        updated = VW.get_user_profile()
        self.assertEqual(updated.get("theme"), "light")

        # Set back to dark
        VW.set_user_profile(
            name=prof.get("name", "Test"),
            field=prof.get("field", "AI"),
            keywords=prof.get("keywords", "ml"),
            theme="dark",
        )
        self.assertEqual(VW.get_user_profile().get("theme"), "dark")

    def test_native_folder_dialog_backend_detected(self):
        backend = VP.native_dialog_backend()
        self.assertIn(backend, ["Windows dialog", "macOS chooser", "Tk dialog", "zenity", "kdialog", "none"])

    def test_evidence_subviews_exclude_user_guide(self):
        # The page registry is the single source of truth for the navigation,
        # so assert against it rather than against a string in a source file.
        import vellum_pages as VP
        evidence = next(s for s in VP.SECTIONS if s["label"] == "🔬 Evidence")
        titles = [p[1] for p in evidence["pages"]]
        self.assertEqual(titles, ["Methodology & Appraisal", "Export Center"])
        self.assertNotIn("User Guide & FAQ", titles)

    def test_developer_credits_dialog_clean(self):
        import inspect
        src = inspect.getsource(VT.show_about_dialog)
        self.assertIn("Amine Zouaghi", src)
        self.assertIn("amine.zouaghi@unipr.it", src)
        self.assertNotIn("User Guide & FAQ", src)
        self.assertNotIn("Profile & Vaults", src)

    def test_discover_subviews_exclude_researchers(self):
        import vellum_pages as VP
        discover = next(s for s in VP.SECTIONS if s["label"] == "🔍 Discover")
        titles = [p[1] for p in discover["pages"]]
        self.assertEqual(titles, ["Literature Search", "Citation Network"])
        self.assertNotIn("Researchers", titles)

        # Researchers is a section of its own, and it is reachable.
        owners = [s for s in VP.SECTIONS if any(p[1] == "Researchers" for p in s["pages"])]
        self.assertEqual(len(owners), 1)
        self.assertEqual(owners[0]["label"], "🔖 Researchers")
        self.assertIn("researchers", VP.PAGES or VP.SECTION_OF)

    def test_every_registered_screen_has_a_unique_url_path(self):
        import vellum_pages as VP
        paths = [p[0] for s in VP.SECTIONS for p in s["pages"]]
        self.assertEqual(len(paths), len(set(paths)), "duplicate url_path in the registry")
        # Streamlit does not support nested URL path segments.
        for p in paths:
            self.assertNotIn("/", p, f"url_path {p!r} must be a single path segment")

    def test_registry_covers_the_documented_screens(self):
        import vellum_pages as VP
        documented = {
            "overview", "discover_literature", "discover_citation", "screening",
            "library_pool", "library_downloader", "evidence_methodology",
            "evidence_export", "notes", "researchers", "guide",
        }
        registered = {p[0] for s in VP.SECTIONS for p in s["pages"]}
        self.assertEqual(registered, documented)

    def test_export_center_datasets_exclude_researchers(self):
        from app_pages import export_center
        self.assertIn("Screened literature records", export_center.DATASETS)
        self.assertIn("Downloaded PDF metadata", export_center.DATASETS)
        self.assertNotIn("Researcher shortlist (works)", export_center.DATASETS)
        self.assertNotIn("Saved researcher profiles", export_center.DATASETS)

    def test_expander_css_dark_and_light(self):
        dark_css = VT.get_theme_css(dark=True)
        self.assertIn('div[data-testid="stExpander"]', dark_css)
        self.assertIn('details[data-testid="stExpander"]', dark_css)

        light_css = VT.get_theme_css(dark=False)
        self.assertIn('div[data-testid="stExpander"]', light_css)
        self.assertIn('details[data-testid="stExpander"]', light_css)

    def test_dataframe_and_download_button_css_in_dark_mode(self):
        dark_css = VT.get_theme_css(dark=True)
        self.assertIn('div[data-testid="stDataFrame"]', dark_css)
        self.assertIn('invert(0.92)', dark_css)
        self.assertIn('div.stDownloadButton > button', dark_css)

    def test_citation_graph_has_bulk_download_and_queue(self):
        with open(BASE_DIR / "app_pages" / "citation_graph.py", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('btn_queue_all_discovered_nodes', content)
        self.assertIn('btn_dl_all_discovered_nodes', content)
        self.assertIn('show_direct_download=True', content)


if __name__ == "__main__":
    unittest.main()


