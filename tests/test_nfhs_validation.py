from dataclasses import replace
from pathlib import Path
from typing import Any

from dhadkan.analytics.validation import IndicatorRow, read_rows, validate_rows

KEY = Path(__file__).parent / "data" / "maharashtra_answer_key.csv"


def good_rows() -> list[IndicatorRow]:
    return read_rows(KEY)


def change(rows: list[IndicatorRow], number: int, **fields: Any) -> list[IndicatorRow]:
    return [replace(r, **fields) if r.indicator_no == number else r for r in rows]


def test_answer_key_is_complete_and_consistent() -> None:
    rows = good_rows()
    assert len(rows) == 12
    assert validate_rows(rows) == []


def test_the_original_copy_mistake_is_caught() -> None:
    rows = change(good_rows(), 84, rural=5.4, total=26.0)
    problems = validate_rows(rows)
    assert any("indicator 84" in p for p in problems)


def test_value_over_100_is_caught() -> None:
    problems = validate_rows(change(good_rows(), 78, total=101.0))
    assert any("not in 0-100" in p for p in problems)


def test_negative_value_is_caught() -> None:
    problems = validate_rows(change(good_rows(), 78, urban=-1.0))
    assert any("not in 0-100" in p for p in problems)


def test_nan_is_caught() -> None:
    problems = validate_rows(change(good_rows(), 78, total=float("nan")))
    assert problems


def test_missing_indicator_is_caught() -> None:
    rows = [r for r in good_rows() if r.indicator_no != 85]
    assert "Maharashtra: indicator 85 missing" in validate_rows(rows)


def test_duplicate_indicator_is_caught() -> None:
    rows = good_rows() + [good_rows()[0]]
    assert any("appears twice" in p for p in validate_rows(rows))


def test_parts_larger_than_whole_is_caught() -> None:
    problems = validate_rows(
        change(
            good_rows(),
            86,
            urban=10.0,
            rural=10.0,
            total=10.0,
        )
    )
    assert any("add up to more than indicator 86" in p for p in problems)


def test_wrong_labels_are_caught() -> None:
    problems = validate_rows(change(good_rows(), 78, topic="blood_pressure"))
    assert any("wrong labels" in p for p in problems)


def test_rounding_tolerance_allows_tiny_differences() -> None:
    assert validate_rows(change(good_rows(), 78, total=6.6)) == []


def test_each_state_is_checked_separately() -> None:
    goa = [replace(r, state="Goa") for r in good_rows()]
    goa = change(goa, 84, rural=5.4, total=26.0)
    problems = validate_rows(good_rows() + goa)
    assert problems
    assert all(p.startswith("Goa") for p in problems)
