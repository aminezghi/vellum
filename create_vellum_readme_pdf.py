"""
create_vellum_readme_pdf.py — Generates a comprehensive, publication-grade README PDF
for Vellum Desktop V2.1 (Fernly Botanical Bento Edition).
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas

PDF_PATH = Path(__file__).resolve().parent / "Vellum_Desktop" / "README_VELLUM_DESKTOP_V2.1.pdf"

# Fernly Botanical Bento Palette
COLOR_PINE = colors.HexColor("#1b4332")
COLOR_SAGE = colors.HexColor("#2d6a4f")
COLOR_MINT = colors.HexColor("#52b788")
COLOR_MINT_PALE = colors.HexColor("#e8f5ed")
COLOR_BG_IVORY = colors.HexColor("#fafcf9")
COLOR_BORDER = colors.HexColor("#dce7e1")
COLOR_TEXT_DARK = colors.HexColor("#1a2e22")
COLOR_TEXT_MUTED = colors.HexColor("#4a5568")
COLOR_PURPLE = colors.HexColor("#7c3aed")
COLOR_AMBER = colors.HexColor("#d97706")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for total page count and professional botanical headers/footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        # Top Header (pages > 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(COLOR_SAGE)
            self.drawString(54, 750, "VELLUM DESKTOP V2.1")
            self.setFont("Helvetica", 8)
            self.setFillColor(COLOR_TEXT_MUTED)
            self.drawString(160, 750, "|   Academic Literature Suite — Fernly Botanical Bento Edition")
            self.setStrokeColor(COLOR_BORDER)
            self.setLineWidth(0.75)
            self.line(54, 742, letter[0] - 54, 742)

        # Bottom Footer
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.75)
        self.line(54, 45, letter[0] - 54, 45)
        self.setFont("Helvetica", 8)
        self.setFillColor(COLOR_TEXT_MUTED)
        self.drawString(54, 32, "Author: Amine Zouaghi (amine.zouaghi@unipr.it)  •  Zero Telemetry  •  100% Local-First")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 32, page_str)
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=COLOR_PINE,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=COLOR_SAGE,
        spaceAfter=14,
    )
    meta_style = ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=COLOR_TEXT_MUTED,
    )
    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=COLOR_PINE,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=COLOR_SAGE,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13.5,
        textColor=COLOR_TEXT_DARK,
        spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4,
    )
    code_style = ParagraphStyle(
        "Code_Custom",
        parent=body_style,
        fontName="Courier",
        fontSize=8.5,
        leading=12,
        textColor=COLOR_PINE,
        backColor=COLOR_MINT_PALE,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=6,
    )

    story = []

    # ── HERO / HEADER BANNER ──────────────────────────────────────────────────
    hero_data = [
        [
            Paragraph("<b>VELLUM DESKTOP V2.1</b>", title_style),
            Paragraph("<b>RELEASE</b><br/>v2.1-STABLE", ParagraphStyle("Badge", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=colors.white, alignment=1)),
        ],
        [
            Paragraph("Academic Literature Discovery, Systematic Review Screening & Citation Analysis Workbench<br/><b>Fernly Botanical Bento Edition</b>", subtitle_style),
            "",
        ],
        [
            Paragraph("<b>Author:</b> Amine Zouaghi (amine.zouaghi@unipr.it) &nbsp;|&nbsp; <b>Institution:</b> University of Parma &nbsp;|&nbsp; <b>Year:</b> 2026", meta_style),
            "",
        ]
    ]
    hero_table = Table(hero_data, colWidths=[400, 104])
    hero_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("BACKGROUND", (1, 0), (1, 0), COLOR_PINE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(hero_table)
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_PINE, spaceBefore=4, spaceAfter=12))

    # ── 1. EXECUTIVE SUMMARY & ARCHITECTURE ───────────────────────────────────
    story.append(Paragraph("1. Executive Summary & Core Philosophy", h1_style))
    story.append(Paragraph(
        "<b>Vellum Desktop V2.1</b> is a self-contained, privacy-first academic research suite designed for researchers, clinicians, and literature synthesis methodologists. "
        "Unlike commercial web platforms that lock bibliographies into proprietary clouds, Vellum operates <b>100% locally on your machine</b>. "
        "Your research vaults, screening decisions, and PDF libraries never leave your local filesystem.",
        body_style,
    ))

    # Bento Feature Grid
    f_data = [
        [
            Paragraph("<b>🧪 ASReview Active Learning</b><br/>Continuous ML literature screening with TF-IDF and Naive Bayes re-ranking. Reduces title/abstract screening effort by up to 70%.", body_style),
            Paragraph("<b>🕸️ Connected Papers Graph</b><br/>Interactive D3 force-directed citation network with seed halo, mint-to-pine temporal gradients, and direct Connected Papers integration.", body_style),
        ],
        [
            Paragraph("<b>🔍 Visual Boolean Builder</b><br/>Federated queries across OpenAlex, Crossref, PubMed, and arXiv with structured WHERE / AND / OR clauses and Scopus/RIS ingestion.", body_style),
            Paragraph("<b>📥 Multi-Engine PDF Downloader</b><br/>Batch paper retrieval with Unpaywall, PubMed Central, and open access resolvers directly into organized project vaults.", body_style),
        ],
    ]
    f_table = Table(f_data, colWidths=[248, 248])
    f_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_IVORY),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(f_table)
    story.append(Spacer(1, 10))

    # ── 2. QUICK START (1-CLICK LAUNCH) ──────────────────────────────────────
    story.append(Paragraph("2. Quick Start: How to Run in 1 Click", h1_style))
    story.append(Paragraph(
        "The suite includes a zero-configuration launcher that requires no manual terminal setup or command-line experience.",
        body_style,
    ))

    story.append(Paragraph("<b>Step 1:</b> Double-click the launch script in the <code>Vellum_Desktop</code> folder:", bullet_style))
    story.append(Paragraph("<code>Vellum_Desktop\\1_launch_desktop_app.bat</code> &nbsp;&nbsp;(or <code>Vellum_Desktop\\CLICK_TO_RUN_VELLUM_DESKTOP.bat</code>)", code_style))
    story.append(Paragraph("<b>Step 2:</b> The script automatically detects the local Python environment and installs any missing packages.", bullet_style))
    story.append(Paragraph("<b>Step 3:</b> Your default browser will launch automatically to the interface:", bullet_style))
    story.append(Paragraph("<code>http://localhost:8501</code>", code_style))

    story.append(Paragraph("<b>Prefer the installer?</b> Double-click <code>Vellum-Desktop-V2.1-Setup-x64.exe</code> — it installs per-user, needs no administrator rights and no Python.", bullet_style))
    story.append(Paragraph(
        "<b>First run:</b> the installer is not code-signed, so Windows SmartScreen shows "
        "\u201cWindows protected your PC\u201d. Choose <b>More info \u2192 Run anyway</b>. To confirm the "
        "file you received is the one that was built, run "
        "<code>certutil -hashfile Vellum-Desktop-V2.1-Setup-x64.exe SHA256</code> and compare it with "
        "<code>DISTRIBUTABLES\\SHA256SUMS.txt</code>.",
        bullet_style,
    ))

    # System Requirements Table
    req_data = [
        ["Component", "Minimum Requirement", "Recommended"],
        ["Operating System", "Windows 10 / 11 (64-bit), macOS, Linux", "Windows 11 (64-bit)"],
        ["Python Environment", "Python 3.10+ (Included in .venv)", "Python 3.11 / 3.13 (.venv pre-configured)"],
        ["Memory (RAM)", "4 GB", "8 GB+ (for active learning models)"],
        ["Web Browser", "Microsoft Edge, Google Chrome, Firefox", "Chromium-based browser (Edge / Chrome)"],
    ]
    req_table = Table(req_data, colWidths=[110, 194, 200])
    req_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PINE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(req_table)
    story.append(Spacer(1, 14))

    # ── 3. MODULE 1: ASREVIEW ACTIVE LEARNING SCREENING ──────────────────────
    story.append(Paragraph("3. Module 1: ASReview Active Learning Screening", h1_style))
    story.append(Paragraph(
        "The <b>ASReview Active Learning Screening Hub</b> (available under the 🧪 Screening tab) brings machine-learning-assisted systematic review screening directly to your desktop. "
        "It follows the official protocol developed by researchers at Utrecht University.",
        body_style,
    ))

    story.append(Paragraph("<b>Key Screening Capabilities:</b>", h2_style))
    story.append(Paragraph("• <b>Multi-Source Ingestion:</b> Import references from Scopus CSV, Web of Science, PubMed, Covidence RIS, BibTeX, or directly from your active Project Paper Pool.", bullet_style))
    story.append(Paragraph("• <b>3-Tier Automated Deduplication:</b> Evaluates incoming papers using Normalized DOI matching, Normalized Title hashing, and Token Jaccard similarity (> 0.88), reporting removed duplicates and preserving metadata.", bullet_style))
    story.append(Paragraph("• <b>Continuous Priority Re-Ranking:</b> Every time you Include (<code>I</code>) or Exclude (<code>E</code>) a study, the underlying TF-IDF + Multinomial Naive Bayes model retrains and dynamically surfaces the most promising candidates first.", bullet_style))
    story.append(Paragraph("• <b>Stopping Heuristic Rules:</b> Monitors consecutive irrelevant records. When 30–50 consecutive negatives are reached, the system signals that the estimated residual recall plateau exceeds 95%.", bullet_style))
    story.append(Paragraph("• <b>Session Management:</b> Create and save independent screening sessions per project (e.g., Primary RCTs, Diagnostic Reviews) with local persistence.", bullet_style))
    story.append(Paragraph("• <b>1-Click Library Export:</b> Send all included studies directly to your project's Unified Paper Pool and download queue.", bullet_style))

    # Keyboard Shortcuts Card
    kb_data = [
        ["Key Shortcut", "Screening Action", "Behavior"],
        ["[ I ]", "⭐ Include Study", "Marks study as relevant, retrains model, re-ranks remaining queue"],
        ["[ E ]", "❌ Exclude Study", "Marks study as irrelevant, increments consecutive exclude counter"],
        ["[ U ]", "↩️ Undo Decision", "Reverts previous label and restores paper to pending queue"],
        ["[ Skip ]", "⏭️ Defer / Skip", "Moves paper to back of pending list without updating ML priors"],
    ]
    kb_table = Table(kb_data, colWidths=[90, 130, 284])
    kb_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_SAGE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(kb_table)
    story.append(Spacer(1, 14))

    # ── 4. MODULE 2: CONNECTED PAPERS FORCE GRAPH ───────────────────────────
    story.append(Paragraph("4. Module 2: Connected Papers Scholarly Force Graph", h1_style))
    story.append(Paragraph(
        "Located in <b>Discover &rarr; Citation Network</b>, this module generates interactive force-directed bibliometric graphs around any seminal seed paper (by DOI or Title).",
        body_style,
    ))
    story.append(Paragraph("• <b>Connected Papers Botanical Styling:</b> Origin seed paper is highlighted with an unmistakable purple halo (<code>#a855f7</code>). Surrounding literature transitions smoothly from pale mint (foundational prior works) to deep forest pine (contemporary derivative breakthroughs).", bullet_style))
    story.append(Paragraph("• <b>Citation-Proportional Radii:</b> Node sizes scale logarithmically based on global citation counts (<code>log10(citations + 1)</code>).", bullet_style))
    story.append(Paragraph("• <b>Direct Connected Papers Deep-Link:</b> Click <b>🕸️ Connected Papers</b> on any selected paper to open its live web graph at <code>https://www.connectedpapers.com/main/{doi}/graph</code>.", bullet_style))
    story.append(Paragraph("• <b>Seamless Screening Handoff:</b> Click <b>🧪 Screen in ASReview</b> on any discovered paper to automatically stage and screen it in your active review session.", bullet_style))
    story.append(Spacer(1, 10))

    # ── 5. MODULE 3: SEARCH, DOWNLOADING & PRISMA ───────────────────────────
    story.append(Paragraph("5. Literature Search, PDF Downloader & PRISMA 2020", h1_style))
    story.append(Paragraph(
        "• <b>Visual Boolean Builder:</b> Construct multi-clause queries (<code>Title / Abstract</code>, <code>Author</code>, <code>Year</code>) connected with uppercase <code>AND</code>, <code>OR</code>, and <code>NOT</code> operators. Automatic syntax validation prevents common API errors.<br/>"
        "• <b>Unified Paper Pool:</b> Deduplicated repository of all candidate studies, featuring instant title search, year filtering, and DOI links.<br/>"
        "• <b>Batch PDF Downloader:</b> Automatically resolves Open Access PDFs via Unpaywall, PubMed Central, and arXiv, saving clean PDF files directly into your project's <code>papers/</code> vault folder.<br/>"
        "• <b>PRISMA 2020 Flow Export:</b> Export complete screening statistics (Identified, Deduplicated, Screened, Excluded, Included) to standard PRISMA-compliant CSV and text summaries.",
        body_style,
    ))
    story.append(Spacer(1, 10))

    # ── 6. DIRECTORY STRUCTURE & COLLABORATION GUIDELINES ────────────────────
    story.append(Paragraph("6. Project Directory Structure & Collaboration", h1_style))
    story.append(Paragraph(
        "When sharing Vellum Desktop V2.1 with colleagues, simply provide the standalone archive. "
        "The project structure is organized as follows:",
        body_style,
    ))

    tree_text = (
        "PDF_Downloader_Dual_Pack/\n"
        "  ├── Vellum_Desktop/                 <-- Application 1, self-contained\n"
        "  │     ├── Vellum-Desktop-V2.1-Setup-x64.exe  <-- Windows installer\n"
        "  │     ├── CLICK_TO_RUN_VELLUM_DESKTOP.bat   <-- 1-Click main launcher\n"
        "  │     ├── 1_launch_desktop_app.bat          <-- Alternative launcher\n"
        "  │     ├── README_VELLUM_DESKTOP_V2.1.pdf    <-- This documentation\n"
        "  │     └── Desktop_App/\n"
        "  │           ├── pdf_downloader_app.py       <-- Main application router\n"
        "  │           ├── vellum_theme.py             <-- Fernly Botanical Bento theme\n"
        "  │           ├── app_pages/\n"
        "  │           │     ├── screening.py          <-- ASReview Active Learning Engine\n"
        "  │           │     ├── citation_graph.py     <-- Connected Papers force graph\n"
        "  │           │     ├── project_overview.py   <-- Dashboard & PRISMA matrix\n"
        "  │           │     └── library.py            <-- Unified Paper Pool\n"
        "  │           ├── requirements.txt            <-- Complete dependencies (UTF-8)\n"
        "  │           ├── build_vellum_windows.spec   <-- PyInstaller build spec\n"
        "  │           ├── installer.iss               <-- Inno Setup installer script\n"
        "  │           └── tests/                      <-- 64 unit tests + page smoke test\n"
        "  └── Vellum_Web/                     <-- Application 2, self-contained\n"
        "        ├── 2_launch_fernly_web_app.bat      <-- Web studio launcher\n"
        "        └── Web_App_Fernly/                 <-- Next.js 16 app (port 3002)"
    )
    story.append(Paragraph(tree_text.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))
    story.append(Spacer(1, 10))

    # ── 7. VERIFICATION & QUALITY ASSURANCE ──────────────────────────────────
    story.append(Paragraph("7. Quality Assurance & Test Verification", h1_style))
    story.append(Paragraph(
        "Vellum Desktop V2.1 is rigorously tested with automated unit and regression suites:",
        body_style,
    ))
    story.append(Paragraph("• <b>Test Command:</b> <code>Desktop_App\\.venv\\Scripts\\python.exe -m pytest -o pythonpath=Desktop_App Desktop_App\\tests -v</code>", bullet_style))
    story.append(Paragraph("• <b>Suite Results:</b> <b>64 passed (100% pass rate)</b> across deduplication, active learning re-ranking, and graph generation.", bullet_style))
    story.append(Paragraph("• <b>Page Smoke Test:</b> <code>Desktop_App\\.venv\\Scripts\\python.exe Desktop_App\\tests\\smoke_app_pages.py</code> runs the main app and all 10 pages in-process through Streamlit's AppTest framework - <b>11 / 11 ran clean</b>, with zero exceptions.", bullet_style))
    story.append(Paragraph("• <b>Bytecode Integrity:</b> All modules compile with zero syntax errors via <code>py_compile</code>.", bullet_style))
    story.append(Paragraph("• <b>Frozen Bundle:</b> The compiled <code>Vellum.exe</code> answers <code>/_stcore/health</code> with HTTP 200 on <code>127.0.0.1</code>.", bullet_style))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF documentation: {PDF_PATH}")


if __name__ == "__main__":
    build_pdf()
