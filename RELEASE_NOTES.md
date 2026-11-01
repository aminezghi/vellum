# Vellum v2.1.0 — Academic Literature & Systematic Review Studio

Welcome to the **v2.1.0 Unified Dual-Platform Release** of **Vellum by Amine**!

Vellum is a 100% local-first academic research suite designed for literature discovery, high-throughput batch harvesting, active-learning screening, citation graph exploration, and PRISMA-compliant evidence synthesis.

---

### 🍏 macOS Distributables (Apple Silicon `arm64` & Intel)

1. **[`Vellum-Desktop-v2.1.0-macOS.dmg`](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Desktop-v2.1.0-macOS.dmg)** (194.0 MB) — **Recommended for macOS**
   - **Native Apple Disk Image (.dmg) Installer** with Drag-to-Applications shortcut.
   - Bundles Python 3.13, Streamlit, PyMuPDF, scikit-learn, and native Cocoa WKWebView desktop frame.
   - **Zero Python or dependency installation required**. Open the DMG and drag `Vellum.app` to Applications.
   - *First-time launch note:* Because Vellum is distributed directly to academic colleagues without an Apple Developer subscription, macOS Gatekeeper may show a verification dialog on first open. Simply **Right-Click `Vellum.app` → Open → click Open** (or go to *System Settings → Privacy & Security → Open Anyway*).

2. **[`Vellum-Desktop-v2.1.0-macOS.zip`](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Desktop-v2.1.0-macOS.zip)** (285.4 MB)
   - Portable, standalone `Vellum.app` bundle in a ZIP archive. Extract anywhere and double-click to launch.

3. **[`Vellum-Web-v2.1.0-macOS.zip`](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Web-v2.1.0-macOS.zip)** (476.1 MB)
   - **Zero-Install Web Studio Package for macOS**.
   - Includes pre-verified portable Node.js runtime (`v20.18.0 LTS`) and native Darwin acceleration binaries (`@next/swc-darwin-arm64`, `sharp`).
   - **No Node.js, no npm, and no administrator rights needed**.
   - Extract anywhere and double-click **`START_VELLUM_WEB.command`** (or open `Vellum Web Studio.app`). Automatically launches and opens `http://localhost:3002`. Stop anytime with **`STOP_VELLUM_WEB.command`**.

---

### 📦 Windows Distributables (Windows 10 / 11 64-bit)

1. **[`Vellum-Desktop-v2.1.0-Windows-x64.exe`](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Desktop-v2.1.0-Windows-x64.exe)** (129.2 MB) — **Recommended for Windows**
   - Native Windows 10/11 Inno Setup installer.
   - Installs cleanly to `%LOCALAPPDATA%\Programs\Vellum Desktop` with Start Menu shortcuts and uninstaller.
   - **Requires zero Python or dependency installation**.

2. **[`Vellum-Desktop-v2.1.0-Windows-x64.zip`](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Desktop-v2.1.0-Windows-x64.zip)** (177.7 MB)
   - Portable, zero-install desktop distribution. Unzip anywhere (or on a USB drive) and double-click `Vellum.exe`.

3. **[`Vellum-Web-v2.1.0-Windows-x64.zip`](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Web-v2.1.0-Windows-x64.zip)** (127.1 MB)
   - Self-contained web studio package for Windows. Includes pre-verified portable Node.js runtime (`v24.22.1 LTS`).
   - Double-click **`START_VELLUM_WEB.bat`** to launch on `http://localhost:3002`. Stop anytime with **`STOP_VELLUM_WEB.bat`**.

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
f6a940db4ad6aad6afda2cc081697b0829b1e47ef8b4014fe3820e2fffa78a9c  Vellum-Desktop-v2.1.0-macOS.dmg
9a9a49c174c50440c0e4815c1e50c828944e9f2613a638d7a869ae8b246034f8  Vellum-Desktop-v2.1.0-macOS.zip
550379990821735050dfcff4b980743c54baf8a32cd7352b4a37b6d779af87c5  Vellum-Desktop-v2.1.0-Windows-x64.exe
cee9fd71eb3452d53e252ac4ff04d73c63aeda5caccb6578a6d80781a2a6dc47  Vellum-Desktop-v2.1.0-Windows-x64.zip
b5a5539f5dae74bcf76386a0fe2cb2c9d76864720ba4ab342657b54c82119678  Vellum-Web-v2.1.0-macOS.zip
b469ca2e4ca1223f31c253db962928246e7517b943d84f9fb5eef71b342beed8  Vellum-Web-v2.1.0-Windows-x64.zip
```
