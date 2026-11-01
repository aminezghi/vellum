# Vellum Web — Academic Research Studio
**Author & Lead Architect: Amine Zouaghi (amine.zouaghi@unipr.it) | University of Parma & University of Bologna**  
*Next.js 16 (Turbopack) / React 19 / Tailwind CSS 4 • macOS & Windows*  
*Local-First • Zero Cloud Accounts • IndexedDB Local Storage*

> 💡 **Looking for the zero-install package (No Node.js required)?**  
> If sharing with colleagues or running without installing Node.js or npm, download the pre-packaged zero-install bundles with embedded portable Node.js runtimes from **[GitHub Releases (v2.1.0)](https://github.com/aminezghi/vellum/releases/latest)**:
> - 🍏 **macOS:** [**Download `Vellum-Web-v2.1.0-macOS.zip`**](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Web-v2.1.0-macOS.zip) *(Extract anywhere & double-click `START_VELLUM_WEB.command`)*
> - 🪟 **Windows:** [**Download `Vellum-Web-v2.1.0-Windows-x64.zip`**](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Web-v2.1.0-Windows-x64.zip) *(Extract anywhere & double-click `START_VELLUM_WEB.bat`)*

---

## 📁 What's in this folder (Source Code & Launchers)

This directory contains the universal Next.js 16 source code for the Vellum Web Studio:

| File / Folder | Target Platform | Description |
| :--- | :--- | :--- |
| **`launch_web_app_macos.command`** | 🍏 macOS | One-click launcher to run the web studio on macOS |
| **`launch_web_app.bat`** | 🪟 Windows | One-click launcher to run the web studio on Windows |
| **`Web_App/`** | 🌐 Universal | Full Next.js 16 source code, React 19 components, API routes, and Dexie.js schema |

---

## 🚀 Running from Source (Developers)

### Option 1: One-Click Launchers
* **macOS:** Double-click **`launch_web_app_macos.command`** (or execute `./launch_web_app_macos.command`).
* **Windows:** Double-click **`launch_web_app.bat`**.

Both scripts automatically start the production server on `http://localhost:3002` and open your default browser.

### Option 2: Standard Node.js / NPM Workflow
```bash
cd Web_App
npm install
npm run dev
```
Open **`http://localhost:3002`** in your browser.
