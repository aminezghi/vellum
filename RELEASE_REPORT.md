# Vellum Release Verification Report

- **Generated:** 2026-10-22 11:13:06
- **Commit:** `unknown`
- **Checks:** 35 passed, 0 failed, 0 skipped

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | git working tree is clean | **PASS** |  |
| 2 | build-critical assets are tracked | **PASS** |  |
| 3 | Windows launchers use CRLF endings | **PASS** |  |
| 4 | pytest Desktop_App/tests | **PASS** | 84 passed |
| 5 | all 10 Streamlit pages + main app render | **PASS** | 11/11 clean |
| 6 | TypeScript type-check (tsc --noEmit) | **PASS** | 0 errors |
| 7 | production build present (.next) | **PASS** | BUILD_ID=8Ijlc7cNofM2PlMOsOWWO |
| 8 | installer artefact exists | **PASS** | 129.2 MB  sha256=5503799908217350... |
| 9 | installer Authenticode status | **PASS** | NotSigned (unsigned installers trigger SmartScreen on first run) |
| 10 | silent install succeeds | **PASS** | exit=0 exe=present |
| 11 | installed Vellum.exe serves /_stcore/health | **PASS** | HTTP 200 after 2.1s on port 8501 |
| 12 | installed app serves the UI shell | **PASS** | HTTP 200, 6467 bytes |
| 13 | installed Vellum.exe opens its native window and serves | **PASS** | native app healthy on port 8501 |
| 14 | silent uninstall removes the install directory | **PASS** | exit=0 |
| 15 | share folder is complete | **PASS** |  |
| 16 | SHA256SUMS.txt verifies every shipped file | **PASS** |  |
| 17 | share folder copies to an arbitrary path | **PASS** | C:\Users\azoua\AppData\Local\Temp\vellum_verify\relocated\Vellum Web (copy) |
| 18 | port 3002 is free before the launch | **PASS** |  |
| 19 | launcher starts the studio (relocated) | **PASS** | HTTP 200 after 15.5s on port 3002 |
| 20 | launcher reported a real startup (not an early exit) | **PASS** | startup banner present |
| 21 | the relocated copy is the one serving | **PASS** | process command line points at the relocated folder |
| 22 | home page renders with the Vellum identity | **PASS** | HTTP 200, 28017 bytes |
| 23 | live search API returns real records (OpenAlex) | **PASS** | HTTP 200, 10 result(s), sources=['openalex'] |
| 24 | trends API returns real records (OpenAlex) | **PASS** | HTTP 200, 8 trending paper(s) |
| 25 | empty query is handled gracefully | **PASS** | HTTP 200, empty query handled |
| 26 | studio stops cleanly on request | **PASS** | port 3002 released |
| 27 | dialogs expose dialog semantics | **PASS** | role="dialog" + aria-modal in the shipped bundle |
| 28 | dialogs carry an accessible name | **PASS** | aria-labelledby + aria-describedby |
| 29 | asynchronous results are announced | **PASS** | aria-live live regions |
| 30 | keyboard focus is visible | **PASS** | :focus-visible rule |
| 31 | reduced motion is honoured | **PASS** | prefers-reduced-motion block |
| 32 | the accent picker is a named listbox | **PASS** | aria-haspopup=listbox + role=listbox |
| 33 | every modal uses the shared accessible primitive | **PASS** |  |
| 34 | dialog focus is not animation-frame-only | **PASS** | focusFirst() also runs synchronously |
| 35 | the desktop keyboard shortcut is actually implemented | **PASS** | a keydown listener exists in keyboard_component/ |

## Distributables

| File | Size | SHA-256 |
|---|---|---|
| Vellum-Desktop-V2.1-Setup-x64.exe | 129.2 MB | `550379990821735050dfcff4b980743c54baf8a32cd7352b4a37b6d779af87c5` |
| Vellum_Standalone_Windows_x64.zip | 177.6 MB | `1ab5995e0269f793c7bdd1f4b95cacdba67f1a9be9527cc98acabe60d3b3699e` |
| Vellum_Desktop_V2.1_Botanical_Bento.zip | 1.6 MB | `23ae366666ba6cda1ef0274257d04cf2928f4fff9cec47e15012c47c734990f4` |
| Vellum_Web_Fernly_Latest_Export.zip | 0.2 MB | `4dbf8e72bafa9a9b6e7807164455f693a4d94ae137805432fc807d97d37aca14` |
| Vellum_Web_Fernly_SHARE.zip | 127.0 MB | `04b7a3cff533c007b4d992b7c5437e198a88f331507c5459a624fa327aa3aa76` |

## How to re-verify independently

```powershell
# checksum of a received file (no tooling needed beyond Windows)
certutil -hashfile Vellum-Desktop-V2.1-Setup-x64.exe SHA256

# full harness on this machine
python tools/verify_release.py
```
