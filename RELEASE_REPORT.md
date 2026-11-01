# Vellum Release Verification Report

- **Generated:** 2026-10-30 21:53:58
- **Commit:** `unknown`
- **Checks:** 31 passed, 1 failed, 1 skipped

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | git working tree is clean | **FAIL** | 56 modified file(s): [' M README_FOR_COLLEAGUES.md', ' M README_FOR_COLLEAGUES.pdf', ' M Vellum_Desktop/CLICK_TO_RUN_STANDALONE_EXE.bat'] |
| 2 | build-critical assets are tracked | **PASS** |  |
| 3 | Windows launchers use CRLF endings | **PASS** |  |
| 4 | pytest Desktop_App/tests | **PASS** | 240 passed |
| 5 | all Streamlit pages + main app render | **PASS** | 12/12 clean |
| 6 | TypeScript type-check (tsc --noEmit) | **PASS** | 0 errors |
| 7 | ESLint (0 errors, 0 warnings) | **PASS** | clean |
| 8 | production build present (.next) | **PASS** | BUILD_ID=a5AUpknzp8N9ycA_hEo6M |
| 9 | installer artefact exists | **PASS** | 129.3 MB  sha256=db0e5e5eced31efe... |
| 10 | installer Authenticode status | **PASS** | NotSigned (unsigned installers trigger SmartScreen on first run) |
| 11 | clean-room install / launch / uninstall | **SKIP** | skipped by request |
| 12 | share folder is complete | **PASS** |  |
| 13 | SHA256SUMS.txt verifies every shipped file | **PASS** |  |
| 14 | share folder copies to an arbitrary path | **PASS** | C:\Users\azoua\AppData\Local\Temp\vellum_verify\relocated\Vellum Web (copy) |
| 15 | port 3002 is free before the launch | **PASS** |  |
| 16 | launcher starts the studio (relocated) | **PASS** | HTTP 200 after 18.3s on port 3002 |
| 17 | launcher reported a real startup (not an early exit) | **PASS** | startup banner present |
| 18 | the relocated copy is the one serving | **PASS** | process command line points at the relocated folder |
| 19 | home page renders with the Vellum identity | **PASS** | HTTP 200, 26865 bytes |
| 20 | live search API returns real records (OpenAlex) | **PASS** | HTTP 200, 10 result(s), sources=['openalex'] |
| 21 | trends API returns real records (OpenAlex) | **PASS** | HTTP 200, 8 trending paper(s) |
| 22 | empty query is handled gracefully | **PASS** | HTTP 200, empty query handled |
| 23 | studio stops cleanly on request | **PASS** | port 3002 released |
| 24 | dialogs expose dialog semantics | **PASS** | role="dialog" + aria-modal in the shipped bundle |
| 25 | dialogs carry an accessible name | **PASS** | aria-labelledby + aria-describedby |
| 26 | asynchronous results are announced | **PASS** | aria-live live regions |
| 27 | keyboard focus is visible | **PASS** | :focus-visible rule |
| 28 | reduced motion is honoured | **PASS** | prefers-reduced-motion block |
| 29 | the accent picker is a named listbox | **PASS** | aria-haspopup=listbox + role=listbox |
| 30 | every modal uses the shared accessible primitive | **PASS** |  |
| 31 | dialog focus is not animation-frame-only | **PASS** | focusFirst() also runs synchronously |
| 32 | the desktop keyboard shortcut is actually implemented | **PASS** | a keydown listener exists in keyboard_component/ |

## Distributables

| File | Size | SHA-256 |
|---|---|---|
| Vellum-Desktop-V2.1-Setup-x64.exe | 129.3 MB | `db0e5e5eced31efe041562b93d8a37adf43d01678502365b7edce041b3044354` |
| Vellum_Standalone_Windows_x64.zip | 177.7 MB | `cee9fd71eb3452d53e252ac4ff04d73c63aeda5caccb6578a6d80781a2a6dc47` |
| Vellum_Desktop_V2.1_Botanical_Bento.zip | 1.6 MB | `26e7fc55e776292aa223371f148b830c06a683798f3c372da4256ccb2e5aaecb` |
| Vellum_Web_Fernly_Latest_Export.zip | 0.2 MB | `b64a60530b07974f545f6432ef20f7682ad2866cc2b2e36c6a20cb9175b96d54` |
| Vellum_Web_Fernly_SHARE.zip | 127.1 MB | `b469ca2e4ca1223f31c253db962928246e7517b943d84f9fb5eef71b342beed8` |

## How to re-verify independently

```powershell
# checksum of a received file (no tooling needed beyond Windows)
certutil -hashfile Vellum-Desktop-V2.1-Setup-x64.exe SHA256

# full harness on this machine
python tools/verify_release.py
```
