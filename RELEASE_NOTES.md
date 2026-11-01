# Vellum v2.1.0 — Academic Literature & Systematic Review Studio

Welcome to the **v2.1.0 Unified Release** of **Vellum by Amine**!

Vellum is a 100% local-first academic research suite designed for literature discovery, high-throughput batch harvesting, active-learning screening, citation graph exploration, and PRISMA-compliant evidence synthesis.

---

### 🍏 macOS Distributables Included (Apple Silicon `arm64` & Intel)

1. **`Vellum_Desktop_macOS.zip`** (285.4 MB)
   - **Standalone Native macOS App (`Vellum.app`)** compiled natively on Apple Silicon.
   - Bundles Python 3.13, Streamlit, PyMuPDF, scikit-learn, and native Cocoa WKWebView desktop frame.
   - **Zero Python or dependency installation required**. Extract, drag `Vellum.app` to Applications or Desktop, and double-click to launch!
   - *First-time launch note:* Because Vellum is distributed directly to academic colleagues without an Apple Developer subscription, macOS Gatekeeper may show a verification dialog on first open. Simply **Right-Click `Vellum.app` → Open → click Open** (or go to *System Settings → Privacy & Security → Open Anyway*).

2. **`Vellum_Web_macOS.zip`** (476.1 MB)
   - **Zero-Install Web Studio Package for macOS**.
   - Includes a pre-configured portable Node.js runtime (`v20.18.0 LTS`) and native Darwin acceleration binaries (`@next/swc-darwin-arm64`, `sharp`).
   - **No Node.js, no npm, and no administrator rights needed**.
   - Extract anywhere and double-click **`START_VELLUM_WEB.command`** (or open `Vellum Web Studio.app`). Automatically launches and opens `http://localhost:3002`.
   - Stop anytime with **`STOP_VELLUM_WEB.command`**.

---

### 📦 Windows Distributables Included (Windows 10 / 11 64-bit)

1. **`Vellum-Desktop-V2.1-Setup-x64.exe`** (129.3 MB)
   - Native Windows 10/11 installer.
   - Installs to `%LOCALAPPDATA%\Programs\Vellum Desktop`. No administrator rights or Python installation required.
   
2. **`Vellum_Standalone_Windows_x64.zip`** (177.7 MB)
   - Portable, zero-install desktop distribution. Unzip anywhere and double-click `Vellum.exe`.

3. **`Vellum_Web_OneClick_Package.zip`** (127.1 MB)
   - Self-contained web studio package. Includes pre-verified portable Node.js runtime (`v24.22.1 LTS`).
   - Double-click `START_VELLUM_WEB.bat` to launch on `http://localhost:3002`.

4. **`Vellum_Desktop_Installer_Windows_x64.zip`** (128.8 MB)
   - Complete installer bundle with offline manuals and batch helpers.

---

### 🌟 Key Highlights in v2.1.0
- **Official Brand Identity**: Integrated the official Folded Folio 3-tone emerald brand mark (`#10B981`, `#059669`, `#34D399`) across web and desktop, with high-resolution Retina app icons (`downloader.icns` on macOS, `downloader.ico` on Windows).
- **Active-Learning Screening**: Fast title/abstract screening with global keyboard shortcuts (`I` include · `E` exclude · `U` undo · `S` skip), automatic multi-tier duplicate detection (DOI, normalized title, and token Jaccard similarity ≥ 0.88), and stopping curve heuristics.
- **Citation Intelligence**: D3 interactive Connected Papers network graph with origin halos, citation weighting, and prior/derivative work splits.
- **Batch Downloader**: Multi-file drag-and-drop bib parser with duplicate merging and multi-tier open-access PDF resolution.
- **Grounded Evidence Notebooks**: Tri-pane research workspace with claim extraction and IndexedDB local storage.
- **100% Local Privacy**: Zero telemetry, no cloud accounts, and all data stays on your machine.

---

### 🛠️ Running from Source (Windows & macOS)

If you prefer running directly from source, clean 1-click launchers are provided at the repository root:

- **Windows**: `launch_desktop.bat`, `launch_web.bat`, or `launch_both.bat`
- **macOS**: `launch_desktop_macos.command`, `launch_web_macos.command`, or `launch_both_macos.command`

---

### 🔐 SHA-256 Checksums
Verified against `DISTRIBUTABLES/SHA256SUMS.txt`:
```text
db0e5e5eced31efe041562b93d8a37adf43d01678502365b7edce041b3044354  Vellum-Desktop-V2.1-Setup-x64.exe
cee9fd71eb3452d53e252ac4ff04d73c63aeda5caccb6578a6d80781a2a6dc47  Vellum_Standalone_Windows_x64.zip
787768b598b9605332f1ea30c5e630ec8b4e7ce2b8a01f930e4b85d95be04583  Vellum_Desktop_Installer_Windows_x64.zip
b469ca2e4ca1223f31c253db962928246e7517b943d84f9fb5eef71b342beed8  Vellum_Web_OneClick_Package.zip
9a9a49c174c50440c0e4815c1e50c828944e9f2613a638d7a869ae8b246034f8  Vellum_Desktop_macOS.zip
b5a5539f5dae74bcf76386a0fe2cb2c9d76864720ba4ab342657b54c82119678  Vellum_Web_macOS.zip
```
