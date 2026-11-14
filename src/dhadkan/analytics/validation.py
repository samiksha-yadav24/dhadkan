"""Consistency checks for NFHS indicator rows (blood sugar, blood pressure).

These checks catch copy and extraction mistakes. They cannot make a number
correct; only the source document does that.
"""

import csv
from dataclasses import dataclass
from pathlib import Path

TOLERANCE = 0.2  # values are rounded to one decimal place
AREAS = ("urban", "rural", "total")

# NFHS-6 state fact sheet indicator numbers -> (topic, sex, category)
INDICATORS: dict[int, tuple[str, str, str]] = {
    78: ("blood_sugar", "women", "high"),
    79: ("blood_sugar", "women", "very_high"),
    80: ("blood_sugar", "women", "high_or_medicated"),
    81: ("blood_sugar", "men", "high"),
    82: ("blood_sugar", "men", "very_high"),
    83: ("blood_sugar", "men", "high_or_medicated"),
    84: ("blood_pressure", "women", "mildly_elevated"),
    85: ("blood_pressure", "women", "moderately_or_severely_elevated"),
    86: ("blood_pressure", "women", "elevated_or_medicated"),
    87: ("blood_pressure", "men", "mildly_elevated"),
    88: ("blood_pressure", "men", "moderately_or_severely_elevated"),
    89: ("blood_pressure", "men", "elevated_or_medicated"),
}

# whole indicator -> the two parts that must not add up to more than it
PARTS_OF: dict[int, tuple[int, int]] = {
    80: (78, 79),
    83: (81, 82),
    86: (84, 85),
    89: (87, 88),
}


@dataclass(frozen=True)
class IndicatorRow:
    survey: str
    state: str
    indicator_no: int
    topic: str
    sex: str
    category: str
    urban: float
    rural: float
    total: float
    nfhs5_total: float | None = None
    source_page: int | None = None
    caution: str = ""

    def value(self, area: str) -> float:
        return {"urban": self.urban, "rural": self.rural, "total": self.total}[area]


def _optional_float(text: str | None) -> float | None:
    return float(text) if text else None


def _optional_int(text: str | None) -> int | None:
    return int(text) if text else None


def read_rows(path: Path) -> list[IndicatorRow]:
    with path.open(encoding="utf-8", newline="") as f:
        return [
            IndicatorRow(
                survey=r["survey"],
                state=r["state"],
                indicator_no=int(r["indicator_no"]),
                topic=r["topic"],
                sex=r["sex"],
                category=r["category"],
                urban=float(r["urban"]),
                rural=float(r["rural"]),
                total=float(r["total"]),
                nfhs5_total=_optional_float(r.get("nfhs5_total")),
                source_page=_optional_int(r.get("source_page")),
                caution=r.get("caution") or "",
            )
            for r in csv.DictReader(f)
        ]


def check_state(state: str, rows: list[IndicatorRow]) -> list[str]:
    problems: list[str] = []
    by_no: dict[int, IndicatorRow] = {}
    for row in rows:
        n = row.indicator_no
        if n in by_no:
            problems.append(f"{state}: indicator {n} appears twice")
        by_no[n] = row
        meta = INDICATORS.get(n)
        if meta is None:
            problems.append(f"{state}: unexpected indicator {n}")
        elif meta != (row.topic, row.sex, row.category):
            problems.append(f"{state}: indicator {n} has the wrong labels")
        for area in AREAS:
            value = row.value(area)
            if not 0.0 <= value <= 100.0:
                problems.append(f"{state}: indicator {n} {area} {value} not in 0-100")
        if row.nfhs5_total is not None and not 0.0 <= row.nfhs5_total <= 100.0:
            problems.append(
                f"{state}: indicator {n} nfhs5_total {row.nfhs5_total} not in 0-100"
            )
        low, high = sorted((row.urban, row.rural))
        if not low - TOLERANCE <= row.total <= high + TOLERANCE:
            problems.append(
                f"{state}: indicator {n} total {row.total} is outside "
                f"the urban/rural range {low}-{high}"
            )
    for n in INDICATORS:
        if n not in by_no:
            problems.append(f"{state}: indicator {n} missing")
    for whole, (a, b) in PARTS_OF.items():
        if whole not in by_no or a not in by_no or b not in by_no:
            continue
        for area in AREAS:
            parts = by_no[a].value(area) + by_no[b].value(area)
            if parts > by_no[whole].value(area) + TOLERANCE:
                problems.append(
                    f"{state}: indicators {a} + {b} ({area}) add up to more "
                    f"than indicator {whole}"
                )
    return problems


def validate_rows(rows: list[IndicatorRow]) -> list[str]:
    by_state: dict[str, list[IndicatorRow]] = {}
    for row in rows:
        by_state.setdefault(row.state, []).append(row)
    problems: list[str] = []
    for state, state_rows in sorted(by_state.items()):
        problems += check_state(state, state_rows)
    return problems
