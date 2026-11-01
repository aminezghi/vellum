import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#556052"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "Vellum Academic Research Studio — System & User Manual")
            self.drawRightString(letter[0] - 54, 755, "Fernly Bento & Dual Pack Edition")
            self.setStrokeColor(colors.HexColor("#d5ddd2"))
            self.setLineWidth(0.6)
            self.line(54, 747, letter[0] - 54, 747)

        # Footer
        self.setStrokeColor(colors.HexColor("#d5ddd2"))
        self.setLineWidth(0.6)
        self.line(54, 45, letter[0] - 54, 45)
        self.drawString(54, 32, "Confidential & Academic Open-Access • Designed by Amine Zouaghi")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 32, page_str)
        self.restoreState()

def build_pdf(filename="README_FOR_COLLEAGUES.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Botanical / Slate Color Palette
    PRIMARY = colors.HexColor("#1b4332")     # Deep Pine
    SECONDARY = colors.HexColor("#2d6a4f")   # Forest Green
    ACCENT = colors.HexColor("#40916c")      # Sage Emerald
    DARK_INK = colors.HexColor("#1a1e1b")    # Slate Ink
    MUTED_INK = colors.HexColor("#4d584c")   # Muted Olive
    PANEL_BG = colors.HexColor("#f4f7f4")    # Light Botanical Panel
    BORDER_CLR = colors.HexColor("#d2ded0")  # Hairline Border

    # Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=MUTED_INK,
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=SECONDARY,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=DARK_INK,
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "BulletCustom",
        parent=body_style,
        leftIndent=15,
        bulletIndent=6,
        spaceAfter=3,
    )

    code_style = ParagraphStyle(
        "CodeInline",
        parent=body_style,
        fontName="Courier-Bold",
        fontSize=8.5,
        leading=11,
        textColor=PRIMARY,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=DARK_INK,
    )

    story = []

    # Title Banner Block
    story.append(Paragraph("🌿 Vellum Research Studio", title_style))
    story.append(Paragraph("System Architecture, Requirements & Comprehensive User Manual for Academic Teams", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=0, spaceAfter=10))

    # Meta Info Card
    meta_data = [
        [
            Paragraph("<b>Author & Lead Architect:</b> Amine Zouaghi", table_cell_style),
            Paragraph("<b>Target OS:</b> Windows 10 / 11 (64-bit)", table_cell_style),
        ],
        [
            Paragraph("<b>Version:</b> 3.0 Production Release", table_cell_style),
            Paragraph("<b>License:</b> 100% Free Open-Access (MIT)", table_cell_style),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL_BG),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER_CLR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary & Edition Overview", h1_style))
    story.append(Paragraph(
        "<b>Vellum</b> is an integrated academic research platform combining heavy offline bibliometrics and high-volume full-text PDF harvesting with modern force-directed citation networks, active machine-learning screening, and systematic evidence synthesis. The suite is distributed as two ready-to-use applications sharing one local-first research workflow:",
        body_style,
    ))

    editions = [
        "<b>Vellum Desktop V2.1 — Fernly Botanical Bento (Port 8501):</b> Native Python/Streamlit workbench capable of parallel downloading 10,000+ DOIs, deduplicating Scopus/WoS/PubMed exports, active-learning screening, citation-force-graph exploration, and local PDF vault management.",
        "<b>Vellum Web — Fernly Botanical Bento (Port 3002):</b> Flagship web workspace featuring the Connected Papers interactive network canvas, ASReview active-learning screening, visual clause-by-clause boolean search, batch multi-tier PDF downloader, and tri-pane systematic notebooks.",
    ]
    for ed in editions:
        story.append(Paragraph(f"• {ed}", bullet_style))

    story.append(Spacer(1, 8))

    # 2. System Prerequisites
    story.append(Paragraph("2. System & Hardware Requirements", h1_style))
    
    req_data = [
        [Paragraph("Category", table_header_style), Paragraph("Specification", table_header_style), Paragraph("Notes & Recommendations", table_header_style)],
        [
            Paragraph("<b>Operating System</b>", table_cell_style),
            Paragraph("Windows 10 / 11 (64-bit)", table_cell_style),
            Paragraph("Windows 10 v1903 or newer recommended", table_cell_style),
        ],
        [
            Paragraph("<b>RAM</b>", table_cell_style),
            Paragraph("4 GB min / 8 GB rec", table_cell_style),
            Paragraph("8 GB optimal for 5,000+ candidate screening datasets", table_cell_style),
        ],
        [
            Paragraph("<b>Desktop Engine</b>", table_cell_style),
            Paragraph("Zero software setup required", table_cell_style),
            Paragraph("Standalone binary included (<code>Vellum.exe</code>). No Python install needed.", table_cell_style),
        ],
        [
            Paragraph("<b>Web Editions</b>", table_cell_style),
            Paragraph("Zero setup (one-click package)<br/>or Node.js 18+ (from source)", table_cell_style),
            Paragraph("The shareable package <code>Vellum_Web_Fernly_SHARE.zip</code> bundles its own portable Node.js runtime, verified against nodejs.org checksums. Running from source still needs Node.js LTS 20+.", table_cell_style),
        ],
        [
            Paragraph("<b>Browser</b>", table_cell_style),
            Paragraph("Chromium / Firefox / Edge", table_cell_style),
            Paragraph("Hardware-accelerated HTML5 canvas enabled for graph physics", table_cell_style),
        ],
        [
            Paragraph("<b>Network</b>", table_cell_style),
            Paragraph("Outbound HTTPS (Port 443)", table_cell_style),
            Paragraph("Connects to OpenAlex, arXiv, Crossref, and Semantic Scholar APIs", table_cell_style),
        ],
    ]

    req_table = Table(req_data, colWidths=[95, 140, 269])
    req_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER_CLR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PANEL_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(req_table)
    story.append(Spacer(1, 10))

    # 3. 1-Click Launchers
    story.append(Paragraph("3. 1-Click Application Launchers", h1_style))
    story.append(Paragraph(
        "Each application lives in its own self-contained folder and can be launched directly without command-line configuration:",
        body_style,
    ))

    launch_data = [
        [Paragraph("File to Double-Click", table_header_style), Paragraph("Target Application", table_header_style), Paragraph("Local URL & Action", table_header_style)],
        [
            Paragraph("<b>Vellum_Desktop\\Vellum-Desktop-V2.1-Setup-x64.exe</b>", code_style),
            Paragraph("Vellum Desktop Installer", table_cell_style),
            Paragraph("Installs per-user, no admin rights • Start Menu + uninstaller", table_cell_style),
        ],
        [
            Paragraph("<b>Vellum_Web\\Vellum_Web_Fernly_SHARE\\START_VELLUM_WEB.bat</b>", code_style),
            Paragraph("Vellum Web — Fernly Bento (one-click package)", table_cell_style),
            Paragraph("The package to send to a colleague • <b>nothing to install</b> • Node.js bundled", table_cell_style),
        ],
        [
            Paragraph("<b>Vellum_Web\\2_launch_fernly_web_app.bat</b>", code_style),
            Paragraph("Vellum Web — Fernly Bento (Flagship)", table_cell_style),
            Paragraph("<code>http://localhost:3002</code> • Force Graph, AI Screening, Boolean Search", table_cell_style),
        ],
        [
            Paragraph("<b>Vellum_Desktop\\1_launch_desktop_app.bat</b>", code_style),
            Paragraph("Vellum Desktop V2.1 Workbench", table_cell_style),
            Paragraph("<code>http://localhost:8501</code> • High-volume batch PDF extraction", table_cell_style),
        ],
        [
            Paragraph("<b>3_launch_both_apps.bat</b>", code_style),
            Paragraph("Dual Suite Concurrent Launch", table_cell_style),
            Paragraph("Boots Desktop (8501) and Web (3002) simultaneously", table_cell_style),
        ],
    ]

    launch_table = Table(launch_data, colWidths=[150, 140, 214])
    launch_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER_CLR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PANEL_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(launch_table)
    story.append(Spacer(1, 10))

    # SmartScreen / integrity note - the two things a colleague asks about
    # when a Windows installer warns them.
    story.append(Paragraph(
        "<b>First run of the installer:</b> it is not code-signed, so Windows SmartScreen shows "
        "\u201cWindows protected your PC\u201d. Choose <b>More info \u2192 Run anyway</b>. To confirm "
        "the file you received is the one that was built, run "
        "<code>certutil -hashfile Vellum-Desktop-V2.1-Setup-x64.exe SHA256</code> and compare it with "
        "<code>DISTRIBUTABLES\\SHA256SUMS.txt</code>.",
        body_style,
    ))
    story.append(Spacer(1, 10))

    # 4. Core Features & Scientific Workflows
    story.append(Paragraph("4. Key Features & Operational Workflows", h1_style))

    features = [
        ("🕸️ Connected Papers Interactive Citation Network:",
         "Provides a 3-panel exploration engine modeled after Connected Papers. Nodes are sized by lifetime citations and colored via a continuous mint-to-pine publication year gradient. Features origin paper halo rings, drag-and-drop Coulomb-Hooke physics, floating navigational guide, and direct tabs for <b>Prior Works</b> (foundational ancestry) and <b>Derivative Works</b> (forward breakthroughs). Any node can be re-centered with <i>'Build graph from this paper'</i>."),
        
        ("🧩 Desktop-Style Clause-by-Clause Visual Boolean Builder:",
         "Located under Academic Search. Allows researchers to build exact queries with an initial <code>WHERE</code> clause followed by <code>AND</code>, <code>OR</code>, and <code>NOT</code> connectors. Field dropdowns automatically map terms to target index tokens (<code>[Title/Abstract]</code>, <code>au:</code>, <code>year:</code>, <code>topic:</code>) with real-time compilation and 1-click execution."),
        
        ("🤖 ASReview Active-Learning Screening Hub:",
         "Enables machine-learning assisted title and abstract screening. Accepts multi-file uploads (.csv, .ris, .bib) with automated deduplication across overlapping sources. Employs TF-IDF feature extraction with Naive Bayes probability ranking, keyboard hotkeys (<code>[I]</code> Include, <code>[E]</code> Exclude, <code>[U]</code> Undo), session saving/switching, and live recall stopping curves."),
        
        ("📥 Multi-Tier Failover PDF Harvesting Engine:",
         "Integrated into both web and desktop versions. Automatically searches across Unpaywall, publisher Open Access APIs, Semantic Scholar, and academic mirrors while bypassing publisher paywall traps. Delivers binary PDFs directly into local browser memory and downloads folder."),
        
        ("📖 Grounded Tri-Pane Evidence Synthesis Workspace:",
         "A local-first systematic review notebook workspace. 100% private and persistent using browser IndexedDB. Left pane stores sources and PDFs; center pane provides an interactive document reader; right pane serves as an evidence synthesis studio for recording verbatim claims and generating citation exports."),
    ]

    for title, desc in features:
        story.append(Paragraph(f"<b>{title}</b> {desc}", body_style))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 8))

    # 5. Troubleshooting & Maintenance
    story.append(Paragraph("5. Troubleshooting & Technical Guidance", h1_style))
    tips = [
        "<b>Port Occupied (EADDRINUSE):</b> If port 3002 is already in use, open PowerShell and terminate previous instances using <code>Get-Process -Name node | Stop-Process -Force</code>, then re-run the launcher.",
        "<b>Data Privacy & Storage:</b> Web notebooks and active screening sessions are stored locally in IndexedDB (Dexie.js). No account, API key, or cloud transmission of personal data is required.",
        "<b>API Rate Limits:</b> Click the <b>'API Tokens'</b> button in the Academic Search hub to supply free personal tokens for OpenAlex, Semantic Scholar, or Crossref for unrestricted high-volume querying.",
    ]
    for tip in tips:
        story.append(Paragraph(f"• {tip}", bullet_style))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Generated PDF: {filename}")

if __name__ == "__main__":
    build_pdf()
