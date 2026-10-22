# Vellum Release Verification Report

- **Generated:** 2026-10-22 04:36:33
- **Commit:** `fa3091e`
- **Checks:** 24 passed, 1 failed, 0 skipped

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | git working tree is clean | **FAIL** | 14 modified file(s) |
| 2 | build-critical assets are tracked | **PASS** |  |
| 3 | Windows launchers use CRLF endings | **PASS** |  |
| 4 | pytest Desktop_App/tests | **PASS** | 64 passed |
| 5 | all 10 Streamlit pages + main app render | **PASS** | 11/11 clean |
| 6 | TypeScript type-check (tsc --noEmit) | **PASS** | 0 errors |
| 7 | production build present (.next) | **PASS** | BUILD_ID=XKdFyDK1Jy-GbAGKPEZm5 |
| 8 | installer artefact exists | **PASS** | 129.2 MB  sha256=b7c864c974c7dbea... |
| 9 | installer Authenticode status | **PASS** | NotSigned (unsigned installers trigger SmartScreen on first run) |
| 10 | silent install succeeds | **PASS** | exit=0 exe=present |
| 11 | installed Vellum.exe serves /_stcore/health | **PASS** | HTTP 200 after 2.1s on port 8501 |
| 12 | installed app serves the UI shell | **PASS** | HTTP 200, 6467 bytes |
| 13 | silent uninstall removes the install directory | **PASS** | exit=0 |
| 14 | share folder is complete | **PASS** |  |
| 15 | SHA256SUMS.txt verifies every shipped file | **PASS** |  |
| 16 | share folder copies to an arbitrary path | **PASS** | C:\Users\azoua\AppData\Local\Temp\vellum_verify\relocated\Vellum Web (copy) |
| 17 | port 3002 is free before the launch | **PASS** |  |
| 18 | launcher starts the studio (relocated) | **PASS** | HTTP 200 after 18.1s on port 3002 |
| 19 | launcher reported a real startup (not an early exit) | **PASS** | startup banner present |
| 20 | the relocated copy is the one serving | **PASS** | process command line points at the relocated folder |
| 21 | home page renders with the Vellum identity | **PASS** | HTTP 200, 28509 bytes |
| 22 | live search API returns real records (OpenAlex) | **PASS** | HTTP 200, 10 result(s), sources=['openalex'] |
| 23 | trends API returns real records (OpenAlex) | **PASS** | HTTP 200, 8 trending paper(s) |
| 24 | empty query is handled gracefully | **PASS** | HTTP 200, empty query handled |
| 25 | studio stops cleanly on request | **PASS** | port 3002 released |

## Distributables

| File | Size | SHA-256 |
|---|---|---|
| Vellum-Desktop-V2.0-Setup-x64.exe | 129.2 MB | `b7c864c974c7dbea1fbbd7b2e4c5e863f9510a10c5ac82d16c09d66659824acc` |
| Vellum_Standalone_Windows_x64.zip | 177.5 MB | `2f3ae4a0d5cc20afd489378060b313329252fee3bb68d10e50d30b843fbe43f5` |
| Vellum_Desktop_V2.0_Botanical_Bento.zip | 1.6 MB | `a61f1bbd6325ec1c1c00067306863a4980d30b3a923ba5f215f7169a04ad538c` |
| Vellum_Web_Fernly_Latest_Export.zip | 0.2 MB | `baa46e99c041b077c7963aa8f6a31b0aef45f39336afb27b9fbc8f94f542e296` |

## How to re-verify independently

```powershell
# checksum of a received file (no tooling needed beyond Windows)
certutil -hashfile Vellum-Desktop-V2.0-Setup-x64.exe SHA256

# full harness on this machine
python tools/verify_release.py
```
