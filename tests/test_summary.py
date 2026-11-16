from pathlib import Path

import pandas as pd
import pytest

from dhadkan.analytics.nfhs import ENTITIES, INDIA
from dhadkan.analytics.summary import (
    TOPICS,
    DataError,
    chart_data,
    check_dataset,
    load_indicators,
    to_table,
    write_table,
)

CSV = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "processed"
    / "nfhs6_indicators.csv"
)


@pytest.fixture(scope="module")
def real() -> pd.DataFrame:
    return load_indicators(CSV)


def test_real_dataset_loads_and_passes_checks(real: pd.DataFrame) -> None:
    check_dataset(real)
    assert len(real) == len(ENTITIES) * 12


def test_maharashtra_blood_pressure_matches_hand_checked_values(
    real: pd.DataFrame,
) -> None:
    data = chart_data(real, "blood_pressure")
    assert data.states.loc["Maharashtra", "women"] == 24.9
    assert data.states.loc["Maharashtra", "men"] == 27.7


def test_maharashtra_blood_sugar_matches_hand_checked_values(
    real: pd.DataFrame,
) -> None:
    data = chart_data(real, "blood_sugar")
    assert data.states.loc["Maharashtra", "women"] == 16.0
    assert data.states.loc["Maharashtra", "men"] == 17.7


@pytest.mark.parametrize("topic", sorted(TOPICS))
def test_india_is_kept_apart_from_the_states(real: pd.DataFrame, topic: str) -> None:
    data = chart_data(real, topic)
    assert INDIA not in data.states.index
    assert len(data.states) == len(ENTITIES) - 1
    assert set(data.india) == {"women", "men"}


@pytest.mark.parametrize("topic", sorted(TOPICS))
def test_states_are_sorted_from_highest_average_down(
    real: pd.DataFrame, topic: str
) -> None:
    means = chart_data(real, topic).states.mean(axis=1).tolist()
    assert means == sorted(means, reverse=True)


def test_order_is_the_same_every_time(real: pd.DataFrame) -> None:
    first = chart_data(real, "blood_pressure").states.index.tolist()
    second = chart_data(real, "blood_pressure").states.index.tolist()
    assert first == second


def test_no_total_is_flagged_in_the_real_data(real: pd.DataFrame) -> None:
    # Chandigarh's parentheses are in the rural column only.
    for topic in TOPICS:
        assert chart_data(real, topic).flagged == frozenset()


def test_flagged_total_is_reported_for_the_right_chart(real: pd.DataFrame) -> None:
    changed = real.copy()
    mask = (changed["state"] == "Goa") & (changed["indicator_no"] == 86)
    changed.loc[mask, "caution"] = "rural,total"
    assert ("Goa", "women") in chart_data(changed, "blood_pressure").flagged
    assert chart_data(changed, "blood_sugar").flagged == frozenset()


def test_rural_only_flag_does_not_flag_the_total(real: pd.DataFrame) -> None:
    changed = real.copy()
    mask = (changed["state"] == "Goa") & (changed["indicator_no"] == 86)
    changed.loc[mask, "caution"] = "rural"
    assert chart_data(changed, "blood_pressure").flagged == frozenset()


def test_missing_state_is_rejected(real: pd.DataFrame) -> None:
    with pytest.raises(DataError, match="Goa"):
        chart_data(real[real["state"] != "Goa"], "blood_pressure")


def test_wrong_row_count_is_rejected(real: pd.DataFrame) -> None:
    gone = (real["state"] == "Goa") & (real["indicator_no"] == 78)
    with pytest.raises(DataError, match="Goa"):
        chart_data(real[~gone], "blood_pressure")


def test_other_survey_is_rejected(real: pd.DataFrame) -> None:
    with pytest.raises(DataError, match="NFHS-6"):
        chart_data(real.assign(survey="NFHS-5"), "blood_pressure")


def test_missing_column_is_rejected(real: pd.DataFrame) -> None:
    with pytest.raises(DataError, match="total"):
        chart_data(real.drop(columns=["total"]), "blood_pressure")


def test_unknown_topic_is_rejected(real: pd.DataFrame) -> None:
    with pytest.raises(DataError, match="unknown topic"):
        chart_data(real, "bmi")


def test_table_has_india_first_and_both_groups(real: pd.DataFrame) -> None:
    table = to_table(chart_data(real, "blood_sugar"))
    assert table.index[0] == INDIA
    assert list(table.columns) == ["women", "men"]
    assert len(table) == len(ENTITIES)


def test_written_table_round_trips(real: pd.DataFrame, tmp_path: Path) -> None:
    data = chart_data(real, "blood_pressure")
    out = tmp_path / "nested" / "table.csv"
    write_table(data, out)
    back = pd.read_csv(out, index_col="state")
    pd.testing.assert_frame_equal(back, to_table(data), check_names=False)
