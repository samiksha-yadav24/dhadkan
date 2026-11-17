from pathlib import Path

import pandas as pd
import pytest

from dhadkan.analytics.charts import (
    notes_for,
    render_svg,
    wrapped_notes,
    write_charts,
)
from dhadkan.analytics.summary import TOPICS, DataError, chart_data, load_indicators

CSV = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "processed"
    / "nfhs6_indicators.csv"
)
MAX_SVG_BYTES = 250_000


@pytest.fixture(scope="module")
def real() -> pd.DataFrame:
    return load_indicators(CSV)


@pytest.mark.parametrize("topic", sorted(TOPICS))
def test_every_chart_states_its_limits(real: pd.DataFrame, topic: str) -> None:
    text = " ".join(notes_for(chart_data(real, topic)))
    assert "NFHS-6" in text
    assert "Adults aged 15 and over" in text
    assert "23-56" in text
    assert "Manipur" in text
    assert "sampling error" in text
    assert "not medical advice" in text


def test_blood_sugar_chart_says_random_not_fasting(real: pd.DataFrame) -> None:
    text = " ".join(notes_for(chart_data(real, "blood_sugar")))
    assert "random (not fasting)" in text
    assert "not diabetes rates" in text


def test_blood_pressure_chart_does_not_mention_sugar_wording(
    real: pd.DataFrame,
) -> None:
    text = " ".join(notes_for(chart_data(real, "blood_pressure")))
    assert "random" not in text


def test_caution_note_only_appears_when_a_total_is_flagged(
    real: pd.DataFrame,
) -> None:
    plain = " ".join(notes_for(chart_data(real, "blood_pressure")))
    assert "25-49" not in plain
    changed = real.copy()
    mask = (changed["state"] == "Goa") & (changed["indicator_no"] == 86)
    changed.loc[mask, "caution"] = "total"
    flagged = " ".join(notes_for(chart_data(changed, "blood_pressure")))
    assert "25-49 unweighted cases" in flagged


def test_notes_are_wrapped_to_the_figure_width(real: pd.DataFrame) -> None:
    lines = wrapped_notes(chart_data(real, "blood_pressure"))
    assert lines
    assert max(len(line) for line in lines) <= 118


@pytest.fixture(scope="module")
def svg_text(real: pd.DataFrame, tmp_path_factory: pytest.TempPathFactory) -> str:
    out = tmp_path_factory.mktemp("charts") / "bp.svg"
    render_svg(chart_data(real, "blood_pressure"), out)
    return out.read_text(encoding="utf-8")


def test_svg_is_a_text_based_image(svg_text: str) -> None:
    assert "<svg" in svg_text
    assert "Adults with elevated blood pressure" in svg_text
    assert "Manipur" in svg_text
    assert "Maharashtra" in svg_text


def test_svg_has_no_scripts_or_embedded_pictures(svg_text: str) -> None:
    assert "<script" not in svg_text
    assert "<image" not in svg_text


def test_svg_carries_a_description_and_no_library_stamp(svg_text: str) -> None:
    assert "Grouped horizontal bar chart" in svg_text
    assert "Matplotlib" not in svg_text


def test_svg_is_small_enough_for_a_phone(svg_text: str) -> None:
    assert len(svg_text.encode("utf-8")) < MAX_SVG_BYTES


def test_same_data_gives_identical_files(real: pd.DataFrame, tmp_path: Path) -> None:
    data = chart_data(real, "blood_sugar")
    first, second = tmp_path / "a.svg", tmp_path / "b.svg"
    render_svg(data, first)
    render_svg(data, second)
    assert first.read_bytes() == second.read_bytes()


def test_india_values_are_in_the_image(real: pd.DataFrame, tmp_path: Path) -> None:
    data = chart_data(real, "blood_sugar")
    out = tmp_path / "s.svg"
    render_svg(data, out)
    svg = out.read_text(encoding="utf-8")
    assert f"India, women ({data.india['women']:.1f})" in svg
    assert f"India, men ({data.india['men']:.1f})" in svg


def test_write_charts_creates_an_svg_and_a_csv_per_topic(
    real: pd.DataFrame, tmp_path: Path
) -> None:
    written = write_charts(real, tmp_path / "out")
    names = sorted(p.name for p in written)
    assert names == [
        "nfhs6_blood_pressure.csv",
        "nfhs6_blood_pressure.svg",
        "nfhs6_blood_sugar.csv",
        "nfhs6_blood_sugar.svg",
    ]
    assert all(p.stat().st_size > 0 for p in written)


def test_write_charts_refuses_a_broken_dataset(
    real: pd.DataFrame, tmp_path: Path
) -> None:
    with pytest.raises(DataError):
        write_charts(real[real["state"] != "Goa"], tmp_path)
    assert not list(tmp_path.iterdir())
