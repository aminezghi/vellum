# Vellum v2.1.0 — Academic Literature & Systematic Review Studio

Welcome to the **v2.1.0 Open-Source Release** of **Vellum by Amine**!

Vellum is a 100% local-first academic research suite designed for literature discovery, high-throughput batch harvesting, active-learning screening, citation graph exploration, and PRISMA-compliant evidence synthesis.

---

### 📦 Windows Distributables Included

1. **`Vellum-Desktop-V2.1-Setup-x64.exe`** (129.3 MB)
   - Native Windows 10/11 installer.
   - Installs to `%LOCALAPPDATA%\Programs\Vellum Desktop`. No administrator rights or Python installation required.
   
2. **`Vellum_Standalone_Windows_x64.zip`** (177.7 MB)
   - Portable, zero-install desktop distribution. Unzip anywhere and double-click `Vellum.exe`.

3. **`Vellum_Web_Fernly_OneClick_Package.zip`** (127.1 MB)
   - Self-contained web studio package. Includes pre-verified portable Node.js runtime (`v24.22.1 LTS`).
   - Double-click `START_VELLUM_WEB.bat` to launch on `http://localhost:3002`.

4. **`Vellum_Desktop_Installer_Windows_x64.zip`** (128.8 MB)
   - Complete installer bundle with offline manuals and batch helpers.

---

### 🌟 Key Highlights in v2.1.0
- **Official Brand Identity**: Integrated the official Folded Folio 3-tone emerald brand mark (`#10B981`, `#059669`, `#34D399`) across web and desktop.
- **Active-Learning Screening**: Fast title/abstract screening with keyboard shortcuts (`I` include · `E` exclude · `U` undo · `S` skip), automatic multi-tier duplicate detection (DOI, normalized title, and token Jaccard similarity ≥ 0.88), and stopping curve heuristics.
- **Citation Intelligence**: D3 interactive Connected Papers network graph with origin halos, citation weighting, and prior/derivative work splits.
- **Batch Downloader**: Multi-file drag-and-drop bib parser with duplicate merging and multi-tier open-access PDF resolution.
- **Grounded Evidence Notebooks**: Tri-pane research workspace with claim extraction and IndexedDB local storage.
- **100% Local Privacy**: Zero telemetry, no cloud accounts, and all data stays on your machine.

---

### 🔐 SHA-256 Checksums
Check against `SHA256SUMS.txt`:
```
db0e5e5eced31efe041562b93d8a37adf43d01678502365b7edce041b3044354  Vellum-Desktop-V2.1-Setup-x64.exe
cee9fd71eb3452d53e252ac4ff04d73c63aeda5caccb6578a6d80781a2a6dc47  Vellum_Standalone_Windows_x64.zip
b469ca2e4ca1223f31c253db962928246e7517b943d84f9fb5eef71b342beed8  Vellum_Web_Fernly_SHARE.zip
```
