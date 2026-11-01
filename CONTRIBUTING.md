# Contributing to Vellum

Thank you for your interest in contributing to **Vellum by Amine**! Vellum is an open-access, local-first academic research suite designed for literature discovery, screening, citation mapping, and evidence synthesis.

---

## 🏛️ Code of Conduct & Core Principles

1. **Local-First & Absolute Privacy**: Never add cloud telemetry, tracking beacons, or forced remote storage. Research data belongs exclusively to the user's machine.
2. **Open Access & Accessibility**: All features adhere to open-science principles and strict web accessibility (WCAG 2.1 AA / dialog semantics / screen-reader announcements).
3. **Reproducibility**: Every build and release must pass the verification harness (`tools/verify_release.py`).

---

## 🛠️ Development Setup

### 1. Vellum Desktop (Python 3.13 + Streamlit)
```powershell
cd Vellum_Desktop\Desktop_App
# Activate existing virtualenv or create a new one
.venv\Scripts\activate
pip install -r requirements.txt

# Run locally in development
streamlit run pdf_downloader_app.py
```

### 2. Vellum Web Studio (Next.js 16 + React 19 + Tailwind CSS)
```powershell
cd Vellum_Web\Web_App
npm install
npm run dev
```
The web studio runs on `http://localhost:3002`.

---

## 🧪 Testing Before Submitting Pull Requests

Every PR must pass automated testing before merging:

```powershell
# 1. Desktop test suite (240 pytest checks + page smoke tests)
& "Vellum_Desktop\Desktop_App\.venv\Scripts\python.exe" -m pytest "Vellum_Desktop\Desktop_App\tests"
& "Vellum_Desktop\Desktop_App\.venv\Scripts\python.exe" "Vellum_Desktop\Desktop_App\tests\smoke_app_pages.py"

# 2. Web studio test suite (64 unit & adversarial tests)
cd Vellum_Web\Web_App
npm test
npm run build
cd ..\..

# 3. Cross-application exchange tests
& "Vellum_Desktop\Desktop_App\.venv\Scripts\python.exe" -m pytest "tools\test_cross_app_exchange.py"
```

---

## 📦 Building Releases

Detailed instructions for building frozen binaries and installers are provided in [`BUILDING.md`](BUILDING.md).

---

## 📄 License

By contributing to Vellum, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
