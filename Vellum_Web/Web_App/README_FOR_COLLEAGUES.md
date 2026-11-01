# 🌿 Vellum Web: Fernly Botanical Edition
## Dedicated Academic Research Studio — Standalone Export Manual

> **Software Version:** 3.0 (Fernly Botanical Edition)  
> **Author & Lead System Architect:** Amine Zouaghi  
> **Target Platform:** Windows 10 / Windows 11 (64-bit)  
> **Runtime Environment:** Next.js 16 (Turbopack) / React 19 / Node.js 18+  
> **Host & Port:** `http://localhost:3002`  
> **License:** 100% Free & Open-Access Academic Tool (MIT License)

---

### 1. Executive Summary

This package is the **dedicated, standalone distribution of the latest Vellum Web Application (Fernly Botanical Bento Edition)**. It contains no legacy desktop binaries or alternate theme prototypes—only the complete, refined web research workstation.

It unites four academic tools into a single, cohesive local-first interface:
1. **Connected Papers Interactive Citation Graph**: Force-directed canvas simulation (Coulomb-Hooke physics) showing origin halo rings, citation-scaled nodes, continuous year gradients, and dedicated **Prior Works** / **Derivative Works** exploratory lists.
2. **ASReview Machine-Learning Title & Abstract Screening**: Active-learning ranking using TF-IDF vectorization and Naive Bayes probability priors with live stopping curves and multi-source deduplication.
3. **Desktop-Style Clause-by-Clause Boolean Search**: Visual clause builder supporting `WHERE`, `AND`, `OR`, `NOT`, and direct index mapping (`[Title/Abstract]`, `au:`, `year:`, `topic:`).
4. **Multi-Tier Batch PDF Downloader**: High-speed binary PDF downloader resolving across Unpaywall, Open Access repositories, and Semantic Scholar with paywall-trapping safeguards.
5. **Grounded Tri-Pane Systematic Notebooks**: Local-first synthesis canvas with client-side IndexedDB persistence, verbatim claim grounding, and citation formatting.

---

### 2. System Requirements & Prerequisites

#### Hardware Requirements
- **CPU:** Dual-Core x86_64 or ARM64 processor (Intel Core i3+, AMD Ryzen, or equivalent).
- **RAM:** 4 GB minimum (8 GB recommended for large 3,000+ candidate screening datasets).
- **Storage:** ~350 MB disk space for the application and dependencies; additional storage for cached PDFs.
- **Display:** 1280 × 800 minimum; 1920 × 1080 (Full HD) recommended for the Tri-Pane Document Reader.

#### Software Prerequisites
- **Operating System:** Windows 10 (version 1903+) or Windows 11 (64-bit).
- **Node.js Runtime:** **Node.js 18.0.0 or higher** (LTS version 20+ strongly recommended).  
  *If not already installed, download it from:* **[https://nodejs.org](https://nodejs.org)** (ensure "Add to PATH" is checked during installation).
- **Web Browser:** Any modern web browser (Google Chrome, Microsoft Edge, Brave, or Mozilla Firefox).

#### Network & Port Access
- **Local Port:** Permitted local connections on port `3002` (`http://localhost:3002`).
- **Outbound HTTPS (Port 443):** Required to fetch academic metadata from OpenAlex, arXiv, Crossref, and Semantic Scholar APIs.

---

### 3. Quick-Start Guide (How to Run)

1. **Extract or Open the Folder:**  
   Open the exported folder (`Vellum_Web_Fernly_Latest/`).

2. **Launch the Application:**  
   Double-click the **`START_VELLUM_WEB.bat`** file in the root folder.
   - The script verifies that Node.js is present.
   - It starts the high-speed Next.js Turbopack development server on port **`3002`**.
   - Your default web browser will automatically open to:  
     👉 **`http://localhost:3002`**

3. **To Stop the Application:**  
   Close the command prompt terminal window running the batch script.

---

### 4. Step-by-Step Feature Walkthrough

#### 4.1. Connected Papers Citation Network
- Navigate to the **"Connected Papers"** tab in the top navigation bar.
- Type any paper title, author name, or DOI into the search field (e.g., *DeepFruits: A Fruit Detection System Using Deep Neural Networks*), or click one of the seminal seed chips.
- **Reading the Graph:**
  - **Origin Paper**: Displayed at the center with a glowing purple ring.
  - **Node Size**: Reflects the paper's total citation volume.
  - **Node Color**: Shows publication timeline (light sage for foundational work, dark forest pine for recent breakthroughs).
  - **Connections**: Clustered by bibliographic and text similarity.
- **Prior Works vs. Derivative Works:**
  - Click **`Prior works`** in the center toolbar to explore the ancestral citations that grounded the field.
  - Click **`Derivative`** to review subsequent advancements and recent applications that cite the cluster.
  - Click **`Build graph from this paper`** in the right-hand inspector to immediately re-center the network around a new discovery.

#### 4.2. Academic Search & Visual Boolean Builder
- Click the **"Academic Search"** tab.
- Select your scientific discipline (Biomedicine, AI & Computer Science, Economics, Climate, Neuroscience, Physics).
- Toggle **`Advanced Search`**:
  - Use the **Visual Boolean Builder** to structure compound queries (`WHERE` concept 1 `AND` concept 2 `NOT` concept 3).
  - Choose specific field targets: `Title / Abstract`, `Author`, `Topic / Keyword`, or `Publication Year`.
  - Review the real-time **`Live Compiled Query`** and click **`Search Literature`**.
- On every result card, click **`Graph`** to jump straight to its Connected Papers visualization, or click **`PDF`** to download the open-access full text.

#### 4.3. Active-Learning Screening Hub (ASReview Engine)
- Navigate to the **"AI Screening"** tab.
- Start a new systematic screening session (give it a title, e.g., *Microplastics Marine Toxicity 2026*).
- Upload candidate records (`.csv`, `.ris`, or `.bib`). Overlapping duplicates across multi-source queries are automatically flagged and resolved.
- Supply 1–3 known relevant articles and 1–3 known irrelevant articles to initialize the Bayesian priors.
- Screen articles using rapid keyboard shortcuts:
  - **`[I]`**: Include / Relevant
  - **`[E]`**: Exclude / Irrelevant
  - **`[U]`**: Undo the last decision
- As you make decisions, the machine learning ranker updates in real time, pushing the most probable relevant articles to the top of your queue so you achieve exhaustive recall early.
- Monitor the **Stopping Curve** and export your final inclusion decisions as PRISMA-compliant CSV or RIS files.

#### 4.4. Batch PDF Downloader
- Access the **"Batch Downloader"** tab.
- Paste a list of DOIs, PubMed PMIDs, or arXiv identifiers (up to hundreds at a time).
- Click **"Start Multi-Source Download"** to trigger parallel multi-tier fetching through Unpaywall, institutional repositories, and open-access publisher APIs.
- Downloaded PDFs can be saved as a consolidated archive or reviewed in the built-in reader.

#### 4.5. Grounded Synthesis Notebooks
- Navigate to **"My Notebooks"** or click on any review workspace.
- The tri-pane layout keeps your evidence corpus (left), document reader (center), and synthesis claims canvas (right) side by side.
- All notes, extracted claims, and citations remain 100% private and persistently stored in your browser's local IndexedDB (`Dexie.js`).

---

### 5. Troubleshooting & Maintenance

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **`Node.js was not found`** | Node.js is not installed or not in PATH | Install Node.js LTS from [nodejs.org](https://nodejs.org) and ensure "Add to PATH" is checked. Restart the terminal. |
| **Port 3002 in use (`EADDRINUSE`)** | Another instance or background process is listening on 3002 | Open PowerShell and run:<br>`Get-Process -Name node \| Stop-Process -Force`<br>Then re-run `START_VELLUM_WEB.bat`. |
| **Blank canvas or slow graph** | Browser hardware acceleration disabled | Enable "Use graphics acceleration when available" in browser settings. |
| **Resetting Workspace Data** | Wanting a clean state without stored data | Click **`Clean Workspace`** on the Dashboard to reset local IndexedDB caches. |

---

*Vellum Web (Fernly Edition) — Designed and architected for academic researchers, systematic review teams, and laboratory investigators.*
