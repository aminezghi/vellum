# <p align="center"><img src="brand-assets/vellum-logo-kit/vectors/vellum-symbol.svg" width="80" height="80" alt="Vellum Logo" /><br/>Vellum by Amine</p>

<p align="center">
  <strong>The 100% Local-First Academic Literature & Systematic Review Studio</strong><br/>
  <em>Zero subscription · Zero cloud tracking · Multi-source discovery across 250M+ papers</em>
</p>

<p align="center">
  <a href="#-quick-download--install-windows"><img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011%20(64--bit)-0078D6?logo=windows" alt="Platform" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-emerald?style=flat" alt="License" /></a>
  <a href="#-testing--verification"><img src="https://img.shields.io/badge/Tests-304%20Passing%20(100%25)-brightgreen" alt="Tests" /></a>
  <a href="RELEASE_REPORT.md"><img src="https://img.shields.io/badge/Release-v2.1.0-blue" alt="Release" /></a>
</p>

---

## 🎬 Product Overview & Demo

[![Vellum Launch Preview](brag-output/vellum-promo-horizontal.jpg)](brag-output/vellum-promo-horizontal.mp4)

> 🎥 **Exploratory Walkthrough:** Watch the 24-second launch tour showcasing the Active-Learning Screening engine, Connected Papers citation graph, grounded evidence extraction, and high-speed multi-source harvesting.

---

## 💡 What is Vellum?

Academic research tools like Rayyan ($480/yr), Connected Papers ($120/yr), and commercial reference managers hold research corpora hostage in the cloud. 

**Vellum by Amine** is an open-source, local-first dual-application research platform designed for independent researchers, PhD candidates, and systematic review teams:

1. **Vellum Web Studio** (`localhost:3002`): Interactive Next.js 16 studio featuring D3/canvas citation graphs, visual Boolean search, active-learning candidate screening, and tri-pane grounded evidence synthesis notebooks.
2. **Vellum Desktop Workbench** (`localhost:8501`): High-throughput native Python 3.13 workbench for bulk PDF batch harvesting, multi-tier open-access resolution (Unpaywall, PubMed Central, arXiv), local vault indexing, and PRISMA 2020 flow reporting.

**Privacy Guarantee:** All PDFs, bibliographic records, IndexedDB notes, and screening decisions remain **100% on your local machine**. No telemetry, no accounts, and no data tracking.

---

## 🚀 Quick Download & Install (Windows)

Choose the setup option that best fits your workflow:

### Option 1: Native Windows Installer (Recommended)
Download **[`Vellum-Desktop-V2.1-Setup-x64.exe`](https://github.com/aminezghi/vellum/releases/latest)**:
- Standard Inno Setup installer for 64-bit Windows 10/11.
- Installs to `%LOCALAPPDATA%\Programs\Vellum Desktop` with Start Menu shortcut and clean uninstaller.
- **Requires no Python or dependency installation**.
- *Note:* Because the binary is self-published without a costly commercial code-signing certificate, Windows SmartScreen may prompt *"Windows protected your PC"*. Click **More info → Run anyway**.

### Option 2: Portable Standalone Desktop ZIP
Download **[`Vellum_Standalone_Windows_x64.zip`](https://github.com/aminezghi/vellum/releases/latest)**:
- Extract anywhere (e.g. `C:\Vellum`) and double-click `Vellum.exe`.
- Zero installation, completely portable on USB drives.

### Option 3: Zero-Install Web Studio (Colleague Share Package)
Download **[`Vellum_Web_Fernly_SHARE.zip`](https://github.com/aminezghi/vellum/releases/latest)**:
- Extract anywhere and double-click **`START_VELLUM_WEB.bat`**.
- Ships with a bundled, pre-verified portable Node.js runtime (`v24.22.1 LTS`).
- **No Node.js, no Python, and no administrator rights needed**. Automatically opens `http://localhost:3002`.
- Stop anytime with a double-click on `STOP_VELLUM_WEB.bat`.

---

## 🛠️ Running from Source

If you prefer building and running directly from the repository:

### 1. Vellum Desktop Workbench
```powershell
# From the repository root
Vellum_Desktop\1_launch_desktop_app.bat
```
Launches `http://localhost:8501` using the configured desktop virtual environment.

### 2. Vellum Web Studio
```powershell
# From the repository root
Vellum_Web\2_launch_fernly_web_app.bat
```
Launches `http://localhost:3002`. Requires Node.js 18+.

---

## 🌟 Key Capabilities

| Capability | Web Studio (`:3002`) | Desktop Workbench (`:8501`) |
| :--- | :---: | :---: |
| **Active-Learning Screening** | Interactive candidate cards, stopping curves, keyboard shortcuts | ASReview-style Bayesian ranking, PRISMA flowcharts |
| **Citation Exploration** | Interactive force graph with prior & derivative works | Litmaps-inspired graph with instant queueing |
| **Multi-Source Discovery** | OpenAlex 250M+ search, trending velocity feeds | OpenAlex, PubMed, arXiv, Crossref with complex Boolean expressions |
| **PDF Harvesting** | Client-side blob retrieval & Unpaywall resolution | High-speed multi-threaded batch download queue |
| **Evidence Extraction** | Tri-pane reader with grounded claim annotations | In-depth text extraction, OCR fallback, notes persistence |
| **Citation Export** | BibTeX, RIS, APA, CSV, JSON | BibTeX, RIS, CSV, PRISMA 2020 metrics |

---

## 🧪 Testing & Verification

Every component and distribution is strictly tested before release:

```powershell
# Comprehensive verification harness (33 tests, end-to-end relocation)
& "Vellum_Desktop\Desktop_App\.venv\Scripts\python.exe" tools\verify_release.py --skip-install

# Desktop Pytest Suite (240 tests)
& "Vellum_Desktop\Desktop_App\.venv\Scripts\python.exe" -m pytest "Vellum_Desktop\Desktop_App\tests"

# Web Studio Test Suite (64 unit & adversarial tests)
cd Vellum_Web\Web_App_Fernly; npm test
```

See [`RELEASE_REPORT.md`](RELEASE_REPORT.md) for the latest execution report and [`BUILDING.md`](BUILDING.md) for build instructions.

---

## 🔐 Checksum Verification

Verify the integrity of downloaded binaries against [`DISTRIBUTABLES/SHA256SUMS.txt`](DISTRIBUTABLES/SHA256SUMS.txt):

```powershell
certutil -hashfile Vellum-Desktop-V2.1-Setup-x64.exe SHA256
```

---

## 🤝 Contributing & Community

Contributions are welcome! Please review [`CONTRIBUTING.md`](CONTRIBUTING.md) for development workflows, testing requirements, and coding conventions.

---

## 👤 Author & Lead Architect

**Amine Zouaghi**
- Academic Researcher & Lead Architect
- Contact: `amine.zouaghi@unipr.it` · [LinkedIn](https://www.linkedin.com/in/zouaghi-amine/)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — free and open-access for academic researchers worldwide.
