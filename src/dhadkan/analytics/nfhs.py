"""Extract blood sugar and blood pressure rows from the NFHS-6 fact sheet PDF.

Parsing is strict on purpose: anything unexpected raises ExtractionError
instead of being guessed. Text functions are separate from the PDF reader so
they can be tested without the PDF.
"""

import csv
import re
from pathlib import Path

import pdfplumber

from dhadkan.analytics.validation import INDICATORS, IndicatorRow, validate_rows

SURVEY = "NFHS-6"
INDIA = "India"
STATES_AND_UTS: tuple[str, ...] = (
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra & Nagar Haveli and Daman & Diu",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "NCT of Delhi",
    "Puducherry",
)
ENTITIES: tuple[str, ...] = (INDIA, *STATES_AND_UTS)

CSV_COLUMNS = [
    "survey",
    "state",
    "indicator_no",
    "topic",
    "sex",
    "category",
    "urban",
    "rural",
    "total",
    "nfhs5_total",
    "source_page",
    "caution",
]

# A key phrase each row's label must contain (spaces removed, lower case).
LABEL_KEYS: dict[int, str] = {
    78: "high(141",
    79: "veryhigh(>160",
    80: "highorveryhigh",
    81: "high(141",
    82: "veryhigh(>160",
    83: "highorveryhigh",
    84: "mildlyelevated",
    85: "moderatelyorseverely",
    86: "elevatedbloodpressure",
    87: "mildlyelevated",
    88: "moderatelyorseverely",
    89: "elevatedbloodpressure",
}
# Words that must NOT appear: rows 86 and 89 are the "whole", not a part.
LABEL_FORBIDDEN: dict[int, tuple[str, ...]] = {
    86: ("mildly", "moderately"),
    89: ("mildly", "moderately"),
}

# Reviewed exceptions: (state, indicator_no) -> why the printed label is accepted.
# Only after checking that PDF page by eye; recorded in docs/data-sources.md.
# The consistency check still requires these values to exceed their two parts.
LABEL_EXCEPTIONS: dict[tuple[str, int], str] = {
    ("Chhattisgarh", 86): (
        "Printed label repeats 'Mildly elevated' from row 84; the values fit "
        "'elevated or taking medication'. Checked by eye on PDF page 49."
    ),
    ("Goa", 86): (
        "Printed label repeats 'Mildly elevated' from row 84; the values fit "
        "'elevated or taking medication'. Checked by eye on PDF page 53."
    ),
}

TITLE_END = "keyindicators"
DASHES = "\u2013\u2014-"
# A line that starts a new row: digits (stray spaces allowed), a dot, and then
# NOT another digit (so a value like "78.5" is not a row start).
ROW_START = re.compile(r"^\s*\d(?:\s?\d){0,2}\s?\.(?!\d)")
# A value is "12.3" or "(12.3)". Parentheses are kept as a caution flag.
VALUE = r"(?:\d{1,3}\.\d|\(\d{1,3}\.\d\))"
FOUR_VALUES = re.compile(rf"({VALUE})\s+({VALUE})\s+({VALUE})\s+({VALUE})\s*$")
VALUE_NAMES = ("urban", "rural", "total", "nfhs5")
MAX_ROW_LINES = 4


class ExtractionError(Exception):
    """The PDF did not look the way the extractor expects."""


def squash(text: str) -> str:
    """Lower-case and remove all whitespace (the PDF has stray spaces)."""
    return re.sub(r"\s+", "", text).lower()


CANONICAL = {squash(name): name for name in ENTITIES}
MARKER = squash("Blood Sugar Level among Adults")


def state_from_title(line: str) -> str | None:
    squashed = squash(line)
    if not squashed.endswith(TITLE_END):
        return None
    return CANONICAL.get(squashed[: -len(TITLE_END)].rstrip(DASHES))


def row_start_pattern(number: int) -> re.Pattern[str]:
    """Match a row's number at the start of a line.

    Tolerates stray spaces inside the number and a missing space after the dot
    ('78.Blood'), but not a decimal value such as '78.5'.
    """
    digits = r"\s?".join(str(number))
    return re.compile(rf"^\s*{digits}\s?\.(?!\d)")


def label_matches(number: int, label: str) -> bool:
    squashed = squash(label)
    if LABEL_KEYS[number] not in squashed:
        return False
    return not any(word in squashed for word in LABEL_FORBIDDEN.get(number, ()))


def parse_value(token: str) -> tuple[float, bool]:
    """Return the number and whether it was printed in parentheses."""
    return float(token.strip("()")), token.startswith("(")


def find_row(
    lines: list[str], number: int
) -> tuple[str, tuple[float, float, float, float], str]:
    """Return label line, four values (urban, rural, total, NFHS-5), caution."""
    start_pattern = row_start_pattern(number)
    start = next((i for i, line in enumerate(lines) if start_pattern.match(line)), None)
    if start is None:
        raise ExtractionError(f"indicator {number}: row not found")
    window = lines[start : start + MAX_ROW_LINES]
    for offset, line in enumerate(window):
        if offset > 0 and ROW_START.match(line):
            break  # reached the next row: never borrow its numbers
        match = FOUR_VALUES.search(line)
        if match:
            parsed = [parse_value(g) for g in match.groups()]
            values = (parsed[0][0], parsed[1][0], parsed[2][0], parsed[3][0])
            caution = ",".join(
                name
                for name, (_, flagged) in zip(VALUE_NAMES, parsed, strict=True)
                if flagged
            )
            return window[0], values, caution
    raise ExtractionError(
        f"indicator {number}: no four numbers found near {window[0]!r}"
    )


def extract_state(
    state: str, text: str, source_page: int | None = None
) -> list[IndicatorRow]:
    """Extract all 12 rows; if anything is wrong, report every problem at once."""
    lines = text.splitlines()
    rows: list[IndicatorRow] = []
    errors: list[str] = []
    for number, (topic, sex, category) in INDICATORS.items():
        try:
            label, (urban, rural, total, nfhs5), caution = find_row(lines, number)
        except ExtractionError as exc:
            errors.append(f"{state}: {exc}")
            continue
        excepted = (state, number) in LABEL_EXCEPTIONS
        if not label_matches(number, label) and not excepted:
            errors.append(
                f"{state}: indicator {number} has an unexpected label: {label!r}"
            )
            continue
        rows.append(
            IndicatorRow(
                survey=SURVEY,
                state=state,
                indicator_no=number,
                topic=topic,
                sex=sex,
                category=category,
                urban=urban,
                rural=rural,
                total=total,
                nfhs5_total=nfhs5,
                source_page=source_page,
                caution=caution,
            )
        )
    if errors:
        raise ExtractionError("\n".join(errors))
    return rows


def find_state_pages(pdf_path: Path) -> dict[str, tuple[int, str]]:
    """Map each state to (PDF page number, page text) for its sugar/BP page."""
    found: dict[str, tuple[int, str]] = {}
    with pdfplumber.open(pdf_path) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text: str = page.extract_text() or ""
            first_line = text.splitlines()[0] if text else ""
            state = state_from_title(first_line)
            if state is None or MARKER not in squash(text):
                continue
            if state in found:
                raise ExtractionError(
                    f"{state}: sheet found twice (pages {found[state][0]}, {index})"
                )
            found[state] = (index, text)
    return found


def extract_pdf(pdf_path: Path) -> list[IndicatorRow]:
    pages = find_state_pages(pdf_path)
    missing = [name for name in ENTITIES if name not in pages]
    if missing:
        raise ExtractionError("sheets not found for: " + ", ".join(missing))
    rows: list[IndicatorRow] = []
    failures: list[str] = []
    for name in ENTITIES:
        page_number, text = pages[name]
        try:
            rows += extract_state(name, text, page_number)
        except ExtractionError as exc:
            failures.append(f"(PDF page {page_number}) {exc}")
    if failures:
        raise ExtractionError("extraction problems:\n" + "\n".join(failures))
    return rows


def write_rows(rows: list[IndicatorRow], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(CSV_COLUMNS)
        for r in rows:
            writer.writerow(
                [
                    r.survey,
                    r.state,
                    r.indicator_no,
                    r.topic,
                    r.sex,
                    r.category,
                    r.urban,
                    r.rural,
                    r.total,
                    "" if r.nfhs5_total is None else r.nfhs5_total,
                    "" if r.source_page is None else r.source_page,
                    r.caution,
                ]
            )


def build_dataset(pdf_path: Path, out_path: Path) -> list[IndicatorRow]:
    """Extract, validate, and write the CSV only if every check passes."""
    rows = extract_pdf(pdf_path)
    problems = validate_rows(rows)
    if problems:
        raise ExtractionError("validation failed:\n" + "\n".join(problems))
    write_rows(rows, out_path)
    return rows
