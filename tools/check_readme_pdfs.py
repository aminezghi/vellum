"""Confirm the generated PDF manuals actually contain the updated guidance.

Extracting the text and probing for the phrases a colleague would look for
catches the classic failure mode: the generator runs, the file is written,
and the content is silently stale.
"""

import sys
from pathlib import Path

from pypdf import PdfReader

REPO = Path(__file__).resolve().parent.parent

PROBES = {
    REPO / "README_FOR_COLLEAGUES.pdf": [
        "START_VELLUM_WEB",
        "Vellum_Web_Fernly_SHARE",
        "SmartScreen",
        "certutil",
        "portable Node",
    ],
    REPO / "Vellum_Desktop" / "README_VELLUM_DESKTOP_V2.1.pdf": [
        "SmartScreen",
        "certutil",
        "Vellum-Desktop-V2.1-Setup-x64.exe",
        "Run anyway",
    ],
}


def main() -> int:
    failures = []
    for pdf, probes in PROBES.items():
        if not pdf.is_file():
            failures.append(f"{pdf.name}: missing")
            continue
        text = "\n".join((p.extract_text() or "") for p in PdfReader(str(pdf)).pages)
        print(f"{pdf.name}  ({len(text)} chars extracted)")
        for probe in probes:
            ok = probe.lower() in text.lower()
            print(f"    {'OK  ' if ok else 'FAIL'}  {probe}")
            if not ok:
                failures.append(f"{pdf.name}: {probe}")
    if failures:
        print("\nFAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nall PDF content probes passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
