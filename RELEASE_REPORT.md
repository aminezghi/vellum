# Vellum Release Verification Report

- **Generated:** 2026-10-22 12:25:38
- **Commit:** `unknown`
- **Checks:** 36 passed, 0 failed, 0 skipped

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | git working tree is clean | **PASS** |  |
| 2 | build-critical assets are tracked | **PASS** |  |
| 3 | Windows launchers use CRLF endings | **PASS** |  |
| 4 | pytest Desktop_App/tests | **PASS** | 84 passed |
| 5 | all 10 Streamlit pages + main app render | **PASS** | 11/11 clean |
| 6 | TypeScript type-check (tsc --noEmit) | **PASS** | 0 errors |
| 7 | ESLint (0 errors, 0 warnings) | **PASS** | clean |
| 8 | production build present (.next) | **PASS** | BUILD_ID=6OfydxPRQ_hGl0teuQHeE |
| 9 | installer artefact exists | **PASS** | 129.2 MB  sha256=5503799908217350... |
| 10 | installer Authenticode status | **PASS** | NotSigned (unsigned installers trigger SmartScreen on first run) |
| 11 | silent install succeeds | **PASS** | exit=0 exe=present |
| 12 | installed Vellum.exe serves /_stcore/health | **PASS** | HTTP 200 after 2.1s on port 8501 |
| 13 | installed app serves the UI shell | **PASS** | HTTP 200, 6467 bytes |
| 14 | installed Vellum.exe opens its native window and serves | **PASS** | native app healthy on port 8501 |
| 15 | silent uninstall removes the install directory | **PASS** | exit=0 |
| 16 | share folder is complete | **PASS** |  |
| 17 | SHA256SUMS.txt verifies every shipped file | **PASS** |  |
| 18 | share folder copies to an arbitrary path | **PASS** | C:\Users\azoua\AppData\Local\Temp\vellum_verify\relocated\Vellum Web (copy) |
| 19 | port 3002 is free before the launch | **PASS** |  |
| 20 | launcher starts the studio (relocated) | **PASS** | HTTP 200 after 21.7s on port 3002 |
| 21 | launcher reported a real startup (not an early exit) | **PASS** | startup banner present |
| 22 | the relocated copy is the one serving | **PASS** | process command line points at the relocated folder |
| 23 | home page renders with the Vellum identity | **PASS** | HTTP 200, 28017 bytes |
| 24 | live search API returns real records (OpenAlex) | **PASS** | HTTP 200, 10 result(s), sources=['openalex'] |
| 25 | trends API returns real records (OpenAlex) | **PASS** | HTTP 200, 8 trending paper(s) |
| 26 | empty query is handled gracefully | **PASS** | HTTP 200, empty query handled |
| 27 | studio stops cleanly on request | **PASS** | port 3002 released |
| 28 | dialogs expose dialog semantics | **PASS** | role="dialog" + aria-modal in the shipped bundle |
| 29 | dialogs carry an accessible name | **PASS** | aria-labelledby + aria-describedby |
| 30 | asynchronous results are announced | **PASS** | aria-live live regions |
| 31 | keyboard focus is visible | **PASS** | :focus-visible rule |
| 32 | reduced motion is honoured | **PASS** | prefers-reduced-motion block |
| 33 | the accent picker is a named listbox | **PASS** | aria-haspopup=listbox + role=listbox |
| 34 | every modal uses the shared accessible primitive | **PASS** |  |
| 35 | dialog focus is not animation-frame-only | **PASS** | focusFirst() also runs synchronously |
| 36 | the desktop keyboard shortcut is actually implemented | **PASS** | a keydown listener exists in keyboard_component/ |

## Distributables

| File | Size | SHA-256 |
|---|---|---|
| Vellum-Desktop-V2.1-Setup-x64.exe | 129.2 MB | `550379990821735050dfcff4b980743c54baf8a32cd7352b4a37b6d779af87c5` |
| Vellum_Standalone_Windows_x64.zip | 177.6 MB | `1ab5995e0269f793c7bdd1f4b95cacdba67f1a9be9527cc98acabe60d3b3699e` |
| Vellum_Desktop_V2.1_Botanical_Bento.zip | 1.6 MB | `23ae366666ba6cda1ef0274257d04cf2928f4fff9cec47e15012c47c734990f4` |
| Vellum_Web_Fernly_Latest_Export.zip | 0.2 MB | `0c525d58ef8f834a599c7c734b471c2e0d68430cef4a1e34d8a520afb0ec4580` |
| Vellum_Web_Fernly_SHARE.zip | 127.0 MB | `5f3ba0f59cff2c9f39dea16872f35bd863330cacaef5aa388330a0bf40f4ffa7` |

## How to re-verify independently

```powershell
# checksum of a received file (no tooling needed beyond Windows)
certutil -hashfile Vellum-Desktop-V2.1-Setup-x64.exe SHA256

# full harness on this machine
python tools/verify_release.py
```
