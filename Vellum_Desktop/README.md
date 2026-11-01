# Vellum Desktop — Academic Literature & Systematic Review Workbench
**Author: Amine Zouaghi (amine.zouaghi@unipr.it) | University of Parma & University of Bologna**  
*Local-First • Zero Telemetry • 100% Privacy-Preserving • macOS & Windows*

> 💡 **Looking for the ready-to-run application?**  
> You do **not** need to install Python or run from source! Download the pre-compiled, self-contained packages directly from **[GitHub Releases (v2.1.0)](https://github.com/aminezghi/vellum/releases/latest)**:
> - 🍏 **macOS:** [**Download `.dmg` Installer**](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Desktop-v2.1.0-macOS.dmg) · [Download `.zip` Portable](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Desktop-v2.1.0-macOS.zip)
> - 🪟 **Windows:** [**Download `.exe` Installer**](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Desktop-v2.1.0-Windows-x64.exe) · [Download `.zip` Portable](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Desktop-v2.1.0-Windows-x64.zip)

---

## 📁 What's in this folder (Source Code & Launchers)

This directory contains the universal cross-platform Python codebase for the Vellum Desktop Workbench:

| File / Folder | Target Platform | Description |
| :--- | :--- | :--- |
| **`launch_desktop_app_macos.command`** | 🍏 macOS | One-click shell script to launch the desktop workbench on macOS |
| **`launch_desktop_app.bat`** | 🪟 Windows | One-click batch script to launch the desktop workbench on Windows |
| **`Desktop_App/`** | 🌐 Universal | Cross-platform Python 3.13 source code (Streamlit + PyMuPDF + scikit-learn) |
| **`Desktop_App/build_vellum_macos.spec`** | 🍏 macOS | PyInstaller specification to build native macOS `.app` bundle |
| **`Desktop_App/build_vellum_windows.spec`** | 🪟 Windows | PyInstaller specification to build native Windows standalone `.exe` |
| **`Desktop_App/installer.iss`** | 🪟 Windows | Inno Setup script to generate the Windows Setup wizard |
| **`README_VELLUM_DESKTOP_V2.1.pdf`** | 📖 Offline Docs | Publication-grade offline manual and user guide |

---

## 🚀 Running from Source (Developers)

### On macOS:
1. Double-click **`launch_desktop_app_macos.command`** (or run `./launch_desktop_app_macos.command` in Terminal).
2. The launcher activates the Python virtual environment and opens the native Vellum window.

### On Windows:
1. Double-click **`launch_desktop_app.bat`**.
2. The launcher boots the Streamlit backend and opens the desktop workbench on `http://localhost:8501`.

---

## 🧪 Running Automated Tests

```bash
cd Desktop_App
pytest tests/
```
All 300+ automated test cases verify citation resolution, active-learning classifier convergence, duplicate detection, and PDF harvest integrity.
