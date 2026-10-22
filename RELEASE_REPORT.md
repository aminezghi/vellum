# Vellum Release Verification Report

- **Generated:** 2026-10-22 05:07:02
- **Commit:** `2511974`
- **Checks:** 24 passed, 2 failed, 0 skipped

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | git working tree is clean | **FAIL** | 8 modified file(s): [' M README_FOR_COLLEAGUES.md', ' M README_FOR_COLLEAGUES.pdf', ' M Vellum_Desktop/README_VELLUM_DESKTOP_V2.0.pdf'] |
| 2 | build-critical assets are tracked | **PASS** |  |
| 3 | Windows launchers use CRLF endings | **FAIL** | LF-only: ['Vellum_Web/Web_App_Fernly/Launch_Web_Fernly.bat', 'Vellum_Web/Web_App_Fernly/START_VELLUM_WEB.bat'] |
| 4 | pytest Desktop_App/tests | **PASS** | 64 passed |
| 5 | all 10 Streamlit pages + main app render | **PASS** | 11/11 clean |
| 6 | TypeScript type-check (tsc --noEmit) | **PASS** | 0 errors |
| 7 | production build present (.next) | **PASS** | BUILD_ID=XKdFyDK1Jy-GbAGKPEZm5 |
| 8 | installer artefact exists | **PASS** | 129.2 MB  sha256=fe0980e050dd01b5... |
| 9 | installer Authenticode status | **PASS** | NotSigned (unsigned installers trigger SmartScreen on first run) |
| 10 | silent install succeeds | **PASS** | exit=0 exe=present |
| 11 | installed Vellum.exe serves /_stcore/health | **PASS** | HTTP 200 after 1.6s on port 8501 |
| 12 | installed app serves the UI shell | **PASS** | HTTP 200, 6467 bytes |
| 13 | installed Vellum.exe opens its native window and serves | **PASS** | native app healthy on port 8501 |
| 14 | silent uninstall removes the install directory | **PASS** | exit=0 |
| 15 | share folder is complete | **PASS** |  |
| 16 | SHA256SUMS.txt verifies every shipped file | **PASS** |  |
| 17 | share folder copies to an arbitrary path | **PASS** | C:\Users\azoua\AppData\Local\Temp\vellum_verify\relocated\Vellum Web (copy) |
| 18 | port 3002 is free before the launch | **PASS** |  |
| 19 | launcher starts the studio (relocated) | **PASS** | HTTP 200 after 14.2s on port 3002 |
| 20 | launcher reported a real startup (not an early exit) | **PASS** | startup banner present |
| 21 | the relocated copy is the one serving | **PASS** | process command line points at the relocated folder |
| 22 | home page renders with the Vellum identity | **PASS** | HTTP 200, 28509 bytes |
| 23 | live search API returns real records (OpenAlex) | **PASS** | HTTP 200, 10 result(s), sources=['openalex'] |
| 24 | trends API returns real records (OpenAlex) | **PASS** | HTTP 200, 8 trending paper(s) |
| 25 | empty query is handled gracefully | **PASS** | HTTP 200, empty query handled |
| 26 | studio stops cleanly on request | **PASS** | port 3002 released |

## Distributables

| File | Size | SHA-256 |
|---|---|---|
| Vellum-Desktop-V2.0-Setup-x64.exe | 129.2 MB | `fe0980e050dd01b5bd1cb899a5ef6d695789339926c369b0c1b4417cdc77f2c5` |
| Vellum_Standalone_Windows_x64.zip | 177.5 MB | `2453e3929bfb944448364f83b5ac0d3511982d6a969644982340721513508cc7` |
| Vellum_Desktop_V2.0_Botanical_Bento.zip | 1.6 MB | `a026e38ee7e086b48a5d008935f85a2941520b433bb37a4c0793ea7bf26c7e29` |
| Vellum_Web_Fernly_Latest_Export.zip | 0.2 MB | `69021fedf8e1608f4ed281997f0c36d306b47cd55a6411c525ad1320490ae726` |
| Vellum_Web_Fernly_SHARE.zip | 127.0 MB | `be27e7f8c78cd7ea5ed9440f53e0b9d3989d7f7605c773ff9a50abc6f66716e8` |

## How to re-verify independently

```powershell
# checksum of a received file (no tooling needed beyond Windows)
certutil -hashfile Vellum-Desktop-V2.0-Setup-x64.exe SHA256

# full harness on this machine
python tools/verify_release.py
```
