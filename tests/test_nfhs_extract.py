from dataclasses import replace
from pathlib import Path

import pytest

from dhadkan.analytics.nfhs import (
    ENTITIES,
    ExtractionError,
    extract_pdf,
    extract_state,
    row_start_pattern,
    state_from_title,
    write_rows,
)
from dhadkan.analytics.validation import IndicatorRow, read_rows, validate_rows

HERE = Path(__file__).parent
KEY_FILE = HERE / "data" / "maharashtra_answer_key.csv"
PDF = HERE.parent / "data" / "raw" / "nfhs6_factsheets.pdf"
needs_pdf = pytest.mark.skipif(not PDF.exists(), reason="NFHS-6 PDF not downloaded")
DADRA = "Dadra & Nagar Haveli and Daman & Diu"


def key_rows() -> dict[int, IndicatorRow]:
    return {r.indicator_no: r for r in read_rows(KEY_FILE)}


def expected_rows() -> list[IndicatorRow]:
    key = key_rows()
    return [key[n] for n in sorted(key)]


def page_text() -> str:
    """A page laid out like the real PDF text, using the hand-checked values."""
    key = key_rows()

    def v(n: int) -> str:
        r = key[n]
        return f"{r.urban} {r.rural} {r.total} {r.nfhs5_total}"

    lines = [
        "Ma harashtra - Ke y Indicators",
        "NFHS-6 NFHS-5",
        "Indicators (2023-24) (2019-21)",
        "Nutritional Status of Adults (age 15-49 years) Urban Rural Total Total",
        "74. Women whose BMI is below normal (%) 13.2 22.5 19.7 18.7",
        "Blood Sugar Level among Adults (age 15 years and above)",
        "Women",
        f"78. Blood sugar level - high (141-160 mg/dl)16 (%) {v(78)}",
        f"79. Blood sugar level - very high (>160 mg/dl)16 (%) {v(79)}",
        "80. Blood sugar level - high or very high (>140 mg/dl) or taking medicine",
        v(80),
        "sugar level16 (%)",
        "Men",
        f"81. Blood sugar level - high (141-160 mg/dl)16 (%) {v(81)}",
        f"82. Blood sugar level - very high (>160 mg/dl)16 (%) {v(82)}",
        "83. Blood sugar level - high or very high (>140 mg/dl) or taking medicine",
        v(83),
        "sugar level16 (%)",
        "Hypertension among Adults (age 15 years and above)",
        "Women",
        "84. Mildly elevated blood pressure (Systolic 140-159 mm of Hg and/or",
        v(84),
        "Diastolic 90-99 mm of Hg) (%)",
        "85. Moderately or severely elevated blood pressure (Systolic >=160 and/or",
        v(85),
        "Diastolic >=100 mm of Hg) (%)",
        "86. Elevated blood pressure (Systolic >=140 and/or Diastolic >=90) or taking",
        v(86),
        "medicine to control blood pressure (%)",
        "Men",
        "87. Mildly elevated blood pressure (Systolic 140-159 mm of Hg and/or",
        v(87),
        "Diastolic 90-99 mm of Hg) (%)",
        "88. Moderately or severely elevated blood pressure (Systolic >=160 and/or",
        v(88),
        "Diastolic >=100 mm of Hg) (%)",
        "89. Elevated blood pressure (Systolic >=140 and/or Diastolic >=90) or taking",
        v(89),
        "medicine to control blood pressure (%)",
        "90. Currently married women in household decisions17 (%) 91.4 88.0 89.0 88.7",
        "16Random blood sugar measurement.",
    ]
    return "\n".join(lines)


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Ma harashtra - Ke y Indicators", "Maharashtra"),
        ("Ha ryana \u2013 Key Indicators", "Haryana"),
        ("Tam il Nadu - Key Indicators", "Tamil Nadu"),
        ("India - Key Indicators", "India"),
        (f"{DADRA} - Key Indicators", DADRA),
        ("[Type here] [Type here] [Type here]", None),
        ("Atlantis - Key Indicators", None),
    ],
)
def test_state_names_survive_stray_spaces(title: str, expected: str | None) -> None:
    assert state_from_title(title) == expected


def test_layout_text_reproduces_the_answer_key() -> None:
    assert extract_state("Maharashtra", page_text()) == expected_rows()


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("78. Blood sugar level - high", True),
        ("7 8. Blood sugar level - high", True),
        ("  78 . Blood sugar", True),
        ("78.5 70.1 74.0 60.0", False),
        ("178. Blood sugar", False),
        ("79. Blood sugar", False),
    ],
)
def test_row_start_tolerates_stray_spaces(line: str, expected: bool) -> None:
    assert (row_start_pattern(78).match(line) is not None) == expected


def test_stray_space_in_row_number_is_tolerated() -> None:
    text = page_text().replace("78. Blood", "7 8. Blood")
    assert extract_state("Maharashtra", text) == expected_rows()


def test_missing_values_do_not_borrow_the_next_row() -> None:
    text = page_text().replace("4.3 3.6 3.9 5.3", "* * * *")
    with pytest.raises(ExtractionError, match="indicator 88"):
        extract_state("Maharashtra", text)


def test_missing_row_is_reported() -> None:
    text = page_text().replace("85. Moderately", "xx. Moderately")
    with pytest.raises(ExtractionError, match="indicator 85: row not found"):
        extract_state("Maharashtra", text)


def test_unexpected_label_is_reported() -> None:
    text = page_text().replace("84. Mildly elevated", "84. Something else")
    with pytest.raises(ExtractionError, match="unexpected label"):
        extract_state("Maharashtra", text)


def test_csv_round_trip(tmp_path: Path) -> None:
    rows = extract_state("Maharashtra", page_text(), source_page=85)
    out = tmp_path / "out" / "rows.csv"
    write_rows(rows, out)
    assert read_rows(out) == rows


def test_parenthesised_value_is_kept_and_flagged() -> None:
    text = page_text().replace("7.4 6.7 7.0 5.7", "7.4 (6.7) 7.0 5.7")
    row = next(r for r in extract_state("Maharashtra", text) if r.indicator_no == 78)
    assert row.urban == 7.4
    assert row.rural == 6.7
    assert row.caution == "rural"


def test_all_problems_in_a_sheet_are_reported_together() -> None:
    text = page_text().replace("84. Mildly", "84. Something")
    text = text.replace("85. Moderately", "xx. Moderately")
    with pytest.raises(ExtractionError) as info:
        extract_state("Maharashtra", text)
    assert "indicator 84" in str(info.value)
    assert "indicator 85" in str(info.value)


def test_caution_survives_csv_round_trip(tmp_path: Path) -> None:
    rows = [replace(r, caution="rural") for r in expected_rows()]
    out = tmp_path / "rows.csv"
    write_rows(rows, out)
    assert read_rows(out) == rows


@pytest.fixture(scope="session")
def real_rows() -> list[IndicatorRow]:
    return extract_pdf(PDF)


@needs_pdf
def test_real_pdf_reproduces_maharashtra_answer_key(
    real_rows: list[IndicatorRow],
) -> None:
    got = [replace(r, source_page=None) for r in real_rows if r.state == "Maharashtra"]
    assert got == expected_rows()


@needs_pdf
def test_real_pdf_covers_every_entity_and_passes_checks(
    real_rows: list[IndicatorRow],
) -> None:
    assert len(real_rows) == len(ENTITIES) * 12
    assert validate_rows(real_rows) == []
