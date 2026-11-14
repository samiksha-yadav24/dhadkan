"""Show how one NFHS PDF page looks to the extractor.

Usage:
    uv run python scripts/debug_state_page.py data/raw/nfhs6_factsheets.pdf 49
"""

import sys
from pathlib import Path

import pdfplumber

from dhadkan.analytics.nfhs import ExtractionError, extract_state, state_from_title


def main(pdf_path: Path, page_number: int) -> None:
    with pdfplumber.open(pdf_path) as pdf:
        text: str = pdf.pages[page_number - 1].extract_text() or ""
    lines = text.splitlines()
    print(f"{len(lines)} lines; first line: {lines[0]!r}")
    start = next((i for i, ln in enumerate(lines) if "Blood" in ln), 0)
    print(f"\n--- lines {start} to {start + 32} (repr shows hidden spaces) ---")
    for i in range(start, min(start + 33, len(lines))):
        print(i, repr(lines[i]))
    state = state_from_title(lines[0]) or "unknown"
    print(f"\nTrying extract_state for: {state}")
    try:
        rows = extract_state(state, text)
        print(f"OK: {len(rows)} rows")
    except ExtractionError as exc:
        print(f"FAILED: {exc}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: debug_state_page.py PDF PAGE_NUMBER")
    main(Path(sys.argv[1]), int(sys.argv[2]))
