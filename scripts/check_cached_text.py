"""Run the extractor on the cached sheet text and write ONE report of every problem.

Usage:
    uv run python scripts/check_cached_text.py
Then open data/raw/problems_report.txt
"""

import json
from pathlib import Path

from dhadkan.analytics.nfhs import ENTITIES, ExtractionError, extract_state
from dhadkan.analytics.validation import IndicatorRow, validate_rows

CACHE = Path("data/raw/nfhs6_page_text.json")
REPORT = Path("data/raw/problems_report.txt")
CONTEXT_LINES = 34


def context(text: str) -> list[str]:
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if "Blood" in ln), 0)
    end = min(start + CONTEXT_LINES, len(lines))
    return [f"{i}: {lines[i]!r}" for i in range(start, end)]


def main() -> None:
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    rows: list[IndicatorRow] = []
    report: list[str] = []
    clean = 0
    for name in ENTITIES:
        if name not in cache:
            report.append(f"MISSING SHEET: {name}")
            continue
        page = cache[name]["page"]
        text = cache[name]["text"]
        try:
            rows += extract_state(name, text, page)
            clean += 1
        except ExtractionError as exc:
            report.append(f"=== {name} (PDF page {page}) ===")
            report.append(f"PROBLEM: {exc}")
            report += context(text)
            report.append("")
    problems = validate_rows(rows)
    if problems:
        report.append("=== CONSISTENCY CHECK PROBLEMS (sheets that were read) ===")
        report += problems
    report.append(f"Sheets extracted cleanly: {clean} of {len(ENTITIES)}")
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report[-3:]))
    print(f"Full report: {REPORT}")


if __name__ == "__main__":
    main()
