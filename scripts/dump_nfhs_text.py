"""Read the NFHS-6 PDF once and cache each sheet's text, so debugging is fast.

Usage:
    uv run python scripts/dump_nfhs_text.py data/raw/nfhs6_factsheets.pdf
"""

import json
import sys
from pathlib import Path

from dhadkan.analytics.nfhs import find_state_pages

OUT = Path("data/raw/nfhs6_page_text.json")


def main(pdf_path: Path) -> None:
    pages = find_state_pages(pdf_path)
    payload = {
        name: {"page": page, "text": text} for name, (page, text) in pages.items()
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Saved {len(payload)} sheets to {OUT}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: dump_nfhs_text.py PATH_TO_PDF")
    main(Path(sys.argv[1]))
