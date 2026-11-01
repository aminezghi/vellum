# Official Vellum Distributables & Downloads

> 💡 **Where are the `.exe`, `.dmg`, and `.zip` files?**  
> In accordance with standard open-source best practices, compiled binary packages are hosted directly under **[GitHub Releases (v2.1.0)](https://github.com/aminezghi/vellum/releases/latest)** to keep the git repository lightweight and fast to clone.

---

## 📦 Official Release Downloads (v2.1.0)

All packages are standalone, pre-verified, and require **zero Python or Node.js installations**:

### 🍏 macOS (Apple Silicon & Intel)

| Package | Format | Size | Description | Download Link |
| :--- | :--- | :--- | :--- | :--- |
| **Vellum Desktop Installer** | `.dmg` | 194.0 MB | Native Apple Disk Image with drag-to-Applications install | [Download `.dmg`](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Desktop-v2.1.0-macOS.dmg) |
| **Vellum Desktop Portable** | `.zip` | 285.4 MB | Standalone portable `Vellum.app` bundle | [Download `.zip`](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Desktop-v2.1.0-macOS.zip) |
| **Vellum Web Studio** | `.zip` | 476.1 MB | Zero-install web studio with portable Node.js runtime | [Download `.zip`](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Web-v2.1.0-macOS.zip) |

---

### 🪟 Windows (10 / 11 64-bit)

| Package | Format | Size | Description | Download Link |
| :--- | :--- | :--- | :--- | :--- |
| **Vellum Desktop Setup** | `.exe` | 129.2 MB | Native Windows Inno Setup installer | [Download `.exe`](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Desktop-v2.1.0-Windows-x64.exe) |
| **Vellum Desktop Portable** | `.zip` | 177.7 MB | Standalone portable `Vellum.exe` bundle | [Download `.zip`](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Desktop-v2.1.0-Windows-x64.zip) |
| **Vellum Web Studio** | `.zip` | 127.1 MB | Zero-install web studio with portable Node.js runtime | [Download `.zip`](https://github.com/aminezghi/vellum/releases/download/v2.1.0/Vellum-Web-v2.1.0-Windows-x64.zip) |

---

## 🔒 Integrity Verification (SHA-256)

To verify the integrity of any downloaded asset against [`SHA256SUMS.txt`](SHA256SUMS.txt):

### macOS / Linux:
```bash
shasum -a 256 -c SHA256SUMS.txt
```

### Windows (PowerShell):
```powershell
Get-FileHash <filename> -Algorithm SHA256
```
Compare the output against the corresponding hash recorded in `SHA256SUMS.txt`.
