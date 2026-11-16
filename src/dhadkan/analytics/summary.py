"""Select and rank the NFHS-6 rows that the charts use (pandas).

Only the Total column is charted. Rows are ordered for readability; the
ordering value is never shown as a statistic.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from dhadkan.analytics.nfhs import ENTITIES, INDIA, SURVEY
from dhadkan.analytics.validation import INDICATORS

# For each chart topic: which indicator number gives each group's value.
# 86 / 89: elevated blood pressure or taking medicine (women / men)
# 80 / 83: blood sugar high or very high or taking medicine (women / men)
TOPICS: dict[str, dict[str, int]] = {
    "blood_pressure": {"women": 86, "men": 89},
    "blood_sugar": {"women": 80, "men": 83},
}
SEXES = ("women", "men")
REQUIRED_COLUMNS = [
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


class DataError(Exception):
    """The dataset is not in the shape the charts need."""


@dataclass(frozen=True, eq=False)
class ChartData:
    topic: str
    india: dict[str, float]
    states: pd.DataFrame  # index: state; columns: women, men
    flagged: frozenset[tuple[str, str]]  # (state, group) whose Total is in ( )


def load_indicators(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"caution": str})
    if "caution" in df.columns:
        df["caution"] = df["caution"].fillna("")
    return df


def check_dataset(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataError("missing columns: " + ", ".join(missing))
    surveys = set(df["survey"])
    if surveys != {SURVEY}:
        raise DataError(f"expected only {SURVEY}, found {sorted(surveys)}")
    found = set(df["state"])
    if found != set(ENTITIES):
        lost = sorted(set(ENTITIES) - found)
        extra = sorted(found - set(ENTITIES))
        raise DataError(f"states differ: missing {lost}, unexpected {extra}")
    counts = df.groupby("state").size()
    short = [str(s) for s in counts.index[counts != len(INDICATORS)]]
    if short:
        raise DataError("wrong number of rows for: " + ", ".join(short))


def chart_data(df: pd.DataFrame, topic: str) -> ChartData:
    if topic not in TOPICS:
        raise DataError(f"unknown topic {topic!r}; choose from {sorted(TOPICS)}")
    check_dataset(df)
    numbers = TOPICS[topic]
    group_of = {number: group for group, number in numbers.items()}
    wanted = df[df["indicator_no"].isin(list(numbers.values()))]
    columns = {}
    for group, number in numbers.items():
        part = wanted[wanted["indicator_no"] == number].set_index("state")
        columns[group] = part["total"].astype(float)
    table = pd.DataFrame(columns)[list(SEXES)]
    india = {group: float(table.loc[INDIA, group]) for group in SEXES}
    states = table.drop(index=INDIA).sort_index()
    order = states.mean(axis=1).sort_values(ascending=False, kind="stable").index
    states = states.loc[order]
    flagged = frozenset(
        (str(row.state), group_of[int(row.indicator_no)])
        for row in wanted.itertuples()
        if "total" in str(row.caution).split(",")
    )
    return ChartData(topic=topic, india=india, states=states, flagged=flagged)


def to_table(data: ChartData) -> pd.DataFrame:
    """India first, then states in chart order; columns women and men."""
    top = pd.DataFrame([data.india], index=[INDIA])[list(SEXES)]
    return pd.concat([top, data.states])


def write_table(data: ChartData, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    to_table(data).to_csv(
        path, index_label="state", float_format="%.1f", lineterminator="\n"
    )
