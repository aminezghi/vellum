"""How-to guide page: the workflow end to end, plus per-page reference."""

from __future__ import annotations

import streamlit as st

PAGES = [
    (":material/travel_explore:", "Literature check",
     "Search ten keyless databases plus Scopus and Web of Science, deduplicate, "
     "screen, and save the project.",
     "Find"),
    (":material/local_library:", "Library",
     "Read PDFs you already have on this computer. Browses a real folder, "
     "previews pages, extracts text, and OCRs scans. No network access.",
     "Find"),
    (":material/download:", "Downloader",
     "Resolve DOIs and links to PDFs, with metadata extraction running in "
     "parallel as files arrive.",
     "Collect"),
    (":material/analytics:", "Analysis & dashboard",
     "Scan for duplicates, inspect the metadata table, and chart your folder by "
     "year, journal and more.",
     "Understand"),
    (":material/manage_search:", "Deep analysis",
     "Read one paper closely: how it sampled, what it measured, which statistics "
     "it reports, and what the text layer cannot show you. Every finding cites "
     "the page it came from.",
     "Understand"),
    (":material/ios_share:", "Export",
     "Save any table as CSV, Excel, JSON or BibTeX, generate a self-contained "
     "notebook for Gemini or Colab, and move it to Drive or Sheets.",
     "Share"),
    (":material/badge:", "My portfolio",
     "Turn screened records and local PDFs into a CV, an HTML summary and a "
     "publication list.",
     "Share"),
]

STEPS = [
    (
        ":material/travel_explore:",
        "Search many databases at once",
        "Open **Literature check**, type a query, and pick your sources. Ten "
        "sources work without any API key — Crossref, OpenAlex, Europe PMC, "
        "PubMed, arXiv, DOAJ, DataCite, Semantic Scholar, OpenAIRE and CORE. "
        "Scopus and Web of Science need your own key, entered in the same panel.",
        "Sources are queried in parallel, so a dozen databases cost about as "
        "long as the slowest one.",
    ),
    (
        ":material/content_copy:",
        "Deduplicate automatically",
        "Records found in several databases are merged by DOI, then by "
        "normalised title. Records with the same title but conflicting DOIs or "
        "years are never silently merged — they are set aside as conflicts for "
        "you to resolve.",
        "The audit table records exactly which records were combined and why.",
    ),
    (
        ":material/checklist:",
        "Screen by hand",
        "Set each record to **include** or **exclude** in the screening table. "
        "Your decisions are saved with the project, so you can stop and come "
        "back later.",
        "Leave rows undecided and they are treated as undecided in the PRISMA "
        "flow rather than being counted as either.",
    ),
    (
        ":material/download:",
        "Hand the queue to the downloader",
        "Press **Load into the downloader tab**. Included records become the "
        "download queue; you are moved to the Downloader page automatically. "
        "Records that carry a direct PDF link are queued by link, so they work "
        "even without a DOI.",
        "You can also paste a `.txt` file of DOIs straight into the Downloader "
        "page instead.",
    ),
    (
        ":material/picture_as_pdf:",
        "Watch the download run",
        "Each article tries every enabled source in turn: your own PDF link, "
        "Unpaywall, Semantic Scholar, OpenAlex, MDPI, the Elsevier API, the "
        "publisher site, PubMed Central and CORE. Stop at any time — finished "
        "files stay on disk.",
        "At the end you get the PDFs, a CSV report, a failed-items list and a "
        "ZIP archive.",
    ),
    (
        ":material/fact_check:",
        "Extract metadata, including scans",
        "After a run, the **Extract metadata** tab reads title, authors, journal, "
        "year and DOI from every PDF. PDFs that are scanned images have no text "
        "layer, so those pages are read with macOS Vision OCR automatically.",
        "OCR only runs on pages that need it, which keeps it fast on normal "
        "PDFs.",
    ),
    (
        ":material/manage_search:",
        "Read one paper closely",
        "The **Deep analysis** page takes a single PDF and reports what it "
        "actually did: data types, sampling strategy, participant "
        "characteristics, instruments, statistics, validity threats, reporting "
        "statements such as ethics and funding, and the shape of the reference "
        "list. The **Search** tab returns the sentences that contain your terms, "
        "with page numbers.",
        "Every finding is a text match shown with the sentence it came from, "
        "never a model's opinion. When the text layer cannot support something — "
        "tables that are images, a truncated download, a methods section it could "
        "not locate — the page says so instead of reporting an absence as if the "
        "authors had done the thing wrong.",
    ),
    (
        ":material/badge:",
        "Turn it into a portfolio",
        "The **My portfolio** page turns screened or downloaded articles into a "
        "researcher profile: citations, h-index, papers per year, top venues "
        "and a formatted publication list, exportable as Markdown, HTML, CSV, "
        "BibTeX or JSON.",
        "It can also read a folder of PDFs directly, so a portfolio works even "
        "if you never run a search.",
    ),
]

KEYS = [
    ("Elsevier / Scopus API key",
     "Optional. From dev.elsevier.com. A personal key raises the entitlement "
     "tier so the full PDF is returned instead of a preview."),
    ("Wiley cookie",
     "Optional. Sign in at onlinelibrary.wiley.com, open an article, then copy "
     "the document's Cookie header from your browser's developer tools."),
    ("Unpaywall email",
     "A real address. Unpaywall uses it to identify requests politely and is "
     "more generous with repeat callers."),
]

FAQ = [
    ("Why is the Start button greyed out?",
     "There is no work queued. Either upload a `.txt` of DOIs, load a queue from "
     "Literature check, or add direct PDF links in the sidebar."),
    ("A DOI failed. What now?",
     "Open **Failed items** in the results panel. Most failures are paywalls, "
     "which need the matching publisher cookie or API key. Raising **Retry "
     "attempts** helps with timeouts."),
    ("Scopus only returns the first author.",
     "That is the free BASIC tier. Adding your own API key unlocks the fuller "
     "record."),
    ("Can I keep my screening decisions?",
     "Yes. Save the project on Literature check; decisions, queries and "
     "filters are stored with it and can be reloaded."),
    ("Does OCR run on every PDF?",
     "No. Streamlit pages that already contain a text layer are read directly. "
     "Only scanned pages are rasterised and sent to OCR."),
    ("Does the Library page send my files anywhere?",
     "No. Browsing, previewing, text extraction and OCR all run locally on your "
     "own machine. The page never makes a network request."),
    ("Will it upload my data to Google Drive or Sheets?",
     "No, and that is deliberate — Vellum never asks for Google credentials. "
     "The Export page downloads a CSV or Excel file and gives you the steps to "
     "move it, or generates a notebook that saves straight into Drive through "
     "Colab without sharing credentials with this app."),
    ("What is the generated notebook?",
     "A plain `.ipynb` with your table embedded inside it as base64. Because "
     "the data travels in the file, it runs in Google Colab or Gemini even if "
     "the CSV never reaches Drive. It contains a few ready-made analysis cells "
     "and prompt suggestions."),
]


def render():
    st.title("How to use")
    st.caption("Vellum — discover literature, explore citation networks, "
               "collect PDFs, analyze evidence, and export datasets.")

    st.markdown("#### :material/account_tree: The pages")
    st.markdown("The sidebar groups the app into five stages. Each page is "
                "independent: jump in wherever your work already is.")
    with st.container(border=True):
        groups: dict[str, list] = {}
        for icon, title, body, group in PAGES:
            groups.setdefault(group, []).append((icon, title, body))
        for group, items in groups.items():
            st.markdown(f"**{group}**")
            for icon, title, body in items:
                st.markdown(f"- :material/check: **{title}** — {body}")

    st.markdown("#### :material/alt_route: The workflow")
    st.markdown("Each step feeds the next. You can also jump straight in at any "
                "point.")
    for icon, title, body, note in STEPS:
        with st.container(border=True):
            st.markdown(f"##### {icon} {title}")
            st.markdown(body)
            st.caption(f"Tip: {note}")

    with st.container(border=True):
        st.markdown("##### :material/key: Optional keys and credentials")
        st.caption("Everything works without these. They only widen what the "
                   "downloader can reach.")
        for name, desc in KEYS:
            st.markdown(f"- **{name}** — {desc}")

    with st.container(border=True):
        st.markdown("##### :material/quiz: Common questions & FAQ")
        for q, a in FAQ:
            with st.expander(q):
                st.markdown(a)

    with st.container(border=True):
        st.markdown("##### :material/code: Developer & Creator Credits")
        st.markdown(
            """
            **Vellum** was created and developed by **Amine Zouaghi** (2026).
            
            - 📧 **Email:** [amine.zouaghi@unipr.it](mailto:amine.zouaghi@unipr.it)
            - 💼 **LinkedIn:** [linkedin.com/in/zouaghi-amine](https://www.linkedin.com/in/zouaghi-amine/)
            - 🏛️ **Affiliation:** University of Parma
            - 🔒 **Privacy:** 100% Local-First. Zero telemetry, zero tracking, all data saved to your local Research Vault.
            """
        )

    with st.container(border=True):
        st.markdown("##### :material/science: What this tool will not do")
        st.markdown(
            "- It does not bypass paywalls you have no right to open. "
            "Authenticated publisher access uses **your own** credentials.\n"
            "- It does not scrape Google Scholar. Results come from documented "
            "APIs and open-access repositories.\n"
            "- Nothing leaves your machine except the API queries you ask for. "
            "There is no telemetry and no account."
        )

    st.divider()
    st.caption(
        "Built with Streamlit. Literature records come from live API queries, so "
        "results depend on what each provider is willing to return at that moment."
    )