import os
from pathlib import Path
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
            self.drawString(54, 755, "Vellum Web: Fernly Botanical Edition — Standalone Research Studio")
            self.drawRightString(letter[0] - 54, 755, "System & User Manual (Port 3002)")
            self.setStrokeColor(colors.HexColor("#d5ddd2"))
            self.setLineWidth(0.6)
            self.line(54, 747, letter[0] - 54, 747)

        # Footer
        self.setStrokeColor(colors.HexColor("#d5ddd2"))
        self.setLineWidth(0.6)
        self.line(54, 45, letter[0] - 54, 45)
        self.drawString(54, 32, "Academic Open-Access Studio • Designed & Engineered by Amine Zouaghi")
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

    # Botanical / Pine Palette
    PRIMARY = colors.HexColor("#1b4332")     # Deep Pine
    SECONDARY = colors.HexColor("#2d6a4f")   # Forest Green
    ACCENT = colors.HexColor("#40916c")      # Sage Emerald
    DARK_INK = colors.HexColor("#1a1e1b")    # Slate Ink
    MUTED_INK = colors.HexColor("#4d584c")   # Muted Olive
    PANEL_BG = colors.HexColor("#f4f7f4")    # Light Botanical Panel
    BORDER_CLR = colors.HexColor("#d2ded0")  # Hairline Border

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=23,
        leading=27,
        textColor=PRIMARY,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        textColor=MUTED_INK,
        spaceAfter=10,
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=PRIMARY,
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=DARK_INK,
        spaceAfter=5,
    )

    bullet_style = ParagraphStyle(
        "BulletCustom",
        parent=body_style,
        leftIndent=14,
        bulletIndent=6,
        spaceAfter=3,
    )

    code_style = ParagraphStyle(
        "CodeInline",
        parent=body_style,
        fontName="Courier-Bold",
        fontSize=8,
        leading=11,
        textColor=PRIMARY,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.8,
        leading=10.5,
        textColor=DARK_INK,
    )

    story = []

    # Title Banner Block
    story.append(Paragraph("🌿 Vellum Web: Fernly Botanical Edition", title_style))
    story.append(Paragraph("Dedicated Standalone Academic Research Studio — User & Technical Requirements Manual", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=0, spaceAfter=8))

    # Meta Info Card
    meta_data = [
        [
            Paragraph("<b>Author & Lead Architect:</b> Amine Zouaghi", table_cell_style),
            Paragraph("<b>Target Platform:</b> Windows 10 / 11 (64-bit)", table_cell_style),
        ],
        [
            Paragraph("<b>Release:</b> Latest Standalone Web App (v3.0)", table_cell_style),
            Paragraph("<b>Host & Port:</b> <code>http://localhost:3002</code>", table_cell_style),
        ],
        [
            Paragraph("<b>Tech Stack:</b> Next.js 16 (Turbopack) / React 19", table_cell_style),
            Paragraph("<b>License:</b> 100% Free Open-Access (MIT)", table_cell_style),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL_BG),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER_CLR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # 1. Overview
    story.append(Paragraph("1. System Overview", h1_style))
    story.append(Paragraph(
        "This distribution contains <b>only the latest standalone web application (Vellum Fernly Botanical Edition)</b>. It combines high-performance interactive bibliometrics with privacy-first evidence synthesis into a single browser-based workstation running on port 3002.",
        body_style,
    ))

    # 2. System Requirements
    story.append(Paragraph("2. System & Hardware Requirements", h1_style))
    req_data = [
        [Paragraph("Category", table_header_style), Paragraph("Requirement", table_header_style), Paragraph("Details & Guidance", table_header_style)],
        [
            Paragraph("<b>Operating System</b>", table_cell_style),
            Paragraph("Windows 10 / 11 (64-bit)", table_cell_style),
            Paragraph("Compatible with Windows 10 (1903+) and Windows 11", table_cell_style),
        ],
        [
            Paragraph("<b>Runtime</b>", table_cell_style),
            Paragraph("Node.js 18.0.0 or higher", table_cell_style),
            Paragraph("Download LTS version (v20+) from <font color='#1b4332'><u>https://nodejs.org</u></font> with PATH checked", table_cell_style),
        ],
        [
            Paragraph("<b>RAM</b>", table_cell_style),
            Paragraph("4 GB min / 8 GB rec", table_cell_style),
            Paragraph("8 GB optimal when screening datasets exceeding 3,000 candidate records", table_cell_style),
        ],
        [
            Paragraph("<b>Web Browser</b>", table_cell_style),
            Paragraph("Chromium / Firefox / Edge", table_cell_style),
            Paragraph("Ensure hardware acceleration is enabled for smooth force-graph canvas physics", table_cell_style),
        ],
        [
            Paragraph("<b>Network</b>", table_cell_style),
            Paragraph("Outbound HTTPS (443)", table_cell_style),
            Paragraph("Connects to OpenAlex, arXiv, Semantic Scholar, and Crossref APIs", table_cell_style),
        ],
    ]
    req_table = Table(req_data, colWidths=[90, 130, 284])
    req_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER_CLR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PANEL_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(req_table)
    story.append(Spacer(1, 8))

    # 3. 1-Click Launch Instructions
    story.append(Paragraph("3. 1-Click Launch Instructions", h1_style))
    story.append(Paragraph(
        "To start the application, double-click the <b><code>START_VELLUM_WEB.bat</code></b> launcher in the root of the folder. The script will:",
        body_style,
    ))
    story.append(Paragraph("1. Verify the Node.js runtime environment.", bullet_style))
    story.append(Paragraph("2. Launch the Next.js 16 Turbopack development server on <b><code>http://localhost:3002</code></b>.", bullet_style))
    story.append(Paragraph("3. Automatically open your default web browser directly to the research studio.", bullet_style))
    story.append(Paragraph("<i>To terminate the session, simply close the command prompt window.</i>", body_style))
    story.append(Spacer(1, 8))

    # 4. Core Features & Scientific Modules
    story.append(Paragraph("4. Core Features & Scientific Modules", h1_style))

    modules = [
        ("🕸️ Connected Papers Force-Directed Citation Network:",
         "Visualizes research clusters using HTML5 canvas with real-time Coulomb-Hooke physics. The origin paper is highlighted by a glowing purple ring, node sizes scale with lifetime citations, and node colors follow a continuous mint-to-pine publication year gradient. Features direct tabs for <b>Prior Works</b> (foundational ancestry) and <b>Derivative Works</b> (subsequent breakthroughs), plus a 1-click <i>'Build graph from this paper'</i> button to branch the network from any node."),

        ("🧩 Desktop-Style Clause-by-Clause Boolean Search:",
         "Located under Academic Search. Allows researchers to build exact queries with an initial <code>WHERE</code> clause followed by <code>AND</code>, <code>OR</code>, and <code>NOT</code> connectors. Field dropdowns automatically map terms to target index tokens (<code>[Title/Abstract]</code>, <code>au:</code>, <code>year:</code>, <code>topic:</code>) with live compilation and 1-click execution."),

        ("🤖 ASReview Active-Learning Screening Hub:",
         "Machine-learning assisted title and abstract screening. Upload candidate bibliographies (.csv, .ris, .bib) with automatic multi-source deduplication. Employs TF-IDF feature extraction with Naive Bayes probability ranking, keyboard hotkeys (<code>[I]</code> Include, <code>[E]</code> Exclude, <code>[U]</code> Uncertain), session saving/switching, and live recall stopping curves."),

        ("📥 Multi-Tier Batch PDF Downloader:",
         "Integrated batch downloader that queries Unpaywall, Open Access repositories, and Semantic Scholar with automated failover and paywall safeguards. Streams PDFs directly into client memory and browser downloads."),

        ("📖 Grounded Tri-Pane Evidence Synthesis Notebooks:",
         "Local-first systematic review workspaces. 100% private and persistent using browser IndexedDB (Dexie.js). Left pane stores sources and PDFs; center pane provides an interactive document reader; right pane serves as an evidence synthesis studio for collecting verbatim claims and generating citation exports."),
    ]

    for title, desc in modules:
        story.append(Paragraph(f"<b>{title}</b> {desc}", body_style))
        story.append(Spacer(1, 2.5))

    story.append(Spacer(1, 8))

    # 5. Troubleshooting & Maintenance
    story.append(Paragraph("5. Troubleshooting & Technical Guidance", h1_style))
    tips = [
        "<b>Port Occupied (EADDRINUSE):</b> If port 3002 is already occupied by a previous session, run <code>Get-Process -Name node | Stop-Process -Force</code> in PowerShell, then re-launch <code>START_VELLUM_WEB.bat</code>.",
        "<b>Data Privacy & Storage:</b> All notebooks, citations, and screening sessions are stored locally in your browser's IndexedDB. No accounts or cloud logins are required.",
        "<b>Workspace Reset:</b> Click <b>'Clean Workspace'</b> on the Dashboard to safely wipe or reset local database caches.",
    ]
    for tip in tips:
        story.append(Paragraph(f"• {tip}", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Generated Standalone Web PDF: {filename}")

if __name__ == "__main__":
    build_pdf(str(Path(__file__).resolve().parent / "README_FOR_COLLEAGUES.pdf"))
