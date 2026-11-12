"""Show where the blood sugar and blood pressure tables sit in an NFHS PDF.

Usage:
    uv run python scripts/explore_nfhs_pdf.py data/raw/nfhs6_factsheets.pdf
"""

import sys
from pathlib import Path

import pdfplumber

MARKER = "Blood Sugar Level among Adults"


def main(pdf_path: Path) -> None:
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Pages in file: {len(pdf.pages)}")
        matches: list[int] = []
        first_text = ""
        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if MARKER not in text:
                continue
            lines = text.splitlines()
            matches.append(index)
            if not first_text:
                first_text = text
            print(f"\n--- file page {index} ---")
            print("first line:", lines[0] if lines else "")
            print("last line :", lines[-1] if lines else "")
        print(f"\nPages containing the marker: {matches}")
        print("\n=== full text of the first matching page ===")
        print(first_text)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: explore_nfhs_pdf.py PATH_TO_PDF")
    main(Path(sys.argv[1]))
