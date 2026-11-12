import pytest
from hypothesis import given
from hypothesis import strategies as st

from dhadkan.risk.idrs import (
    MAX_SCORE,
    SCREENING_CUTOFF,
    FamilyHistory,
    IdrsInput,
    Sex,
    activity_points,
    age_points,
    calculate,
    summary,
    waist_points,
)

FEMALE, MALE = Sex.FEMALE, Sex.MALE
NONE = FamilyHistory.NONE
ONE = FamilyHistory.ONE_PARENT
BOTH = FamilyHistory.BOTH_PARENTS

FORBIDDEN = [
    "you have diabetes",
    "you are diabetic",
    "you will develop",
    "you will get",
    "you are likely to have",
    "heart attack risk is",
]


@pytest.mark.parametrize(
    ("age", "points"),
    [(18, 0), (34, 0), (35, 20), (49, 20), (50, 30), (110, 30)],
)
def test_age_boundaries(age: int, points: int) -> None:
    assert age_points(age) == points


@pytest.mark.parametrize(
    ("waist", "sex", "points"),
    [
        (79.9, FEMALE, 0),
        (80.0, FEMALE, 10),
        (89.9, FEMALE, 10),
        (90.0, FEMALE, 20),
        (89.9, MALE, 0),
        (90.0, MALE, 10),
        (99.9, MALE, 10),
        (100.0, MALE, 20),
    ],
)
def test_waist_boundaries(waist: float, sex: Sex, points: int) -> None:
    assert waist_points(waist, sex) == points


@pytest.mark.parametrize(
    ("exercise", "work", "points"),
    [(True, True, 0), (True, False, 20), (False, True, 20), (False, False, 30)],
)
def test_activity_points(exercise: bool, work: bool, points: int) -> None:
    assert activity_points(exercise, work) == points


# The seven worked examples in Table 3 of S6 (p.761).
TABLE_3 = [
    (MALE, 60, 101.0, True, False, BOTH, 90),
    (FEMALE, 53, 88.0, True, False, ONE, 70),
    (MALE, 45, 92.0, True, False, ONE, 60),
    (FEMALE, 47, 79.0, False, True, ONE, 50),
    (MALE, 32, 96.0, False, False, NONE, 40),
    (FEMALE, 29, 77.0, True, False, NONE, 20),
    (MALE, 25, 80.0, True, True, NONE, 0),
]


@pytest.mark.parametrize(
    ("sex", "age", "waist", "exercise", "work", "family", "expected"), TABLE_3
)
def test_paper_table_3_examples(
    sex: Sex,
    age: int,
    waist: float,
    exercise: bool,
    work: bool,
    family: FamilyHistory,
    expected: int,
) -> None:
    result = calculate(IdrsInput(age, sex, waist, exercise, work, family))
    assert result.total == expected
    assert result.at_or_above_cutoff == (expected >= SCREENING_CUTOFF)


def test_minimum_and_maximum_scores() -> None:
    low = calculate(IdrsInput(25, MALE, 80.0, True, True, NONE))
    high = calculate(IdrsInput(50, MALE, 100.0, False, False, BOTH))
    assert low.total == 0
    assert high.total == MAX_SCORE


@pytest.mark.parametrize("age", [17, 111])
def test_age_out_of_range_rejected(age: int) -> None:
    with pytest.raises(ValueError, match="age"):
        age_points(age)


@pytest.mark.parametrize("waist", [39.9, 200.1, float("nan")])
def test_waist_out_of_range_rejected(waist: float) -> None:
    with pytest.raises(ValueError, match="waist"):
        waist_points(waist, MALE)


def test_summary_above_cutoff_suggests_screening() -> None:
    text = summary(calculate(IdrsInput(60, MALE, 101.0, True, False, BOTH)))
    assert "Your score is 90 out of 100." in text
    assert "screening" in text
    assert "not a diagnosis" in text
    assert "not heart attack risk" in text
    assert "17%" in text


def test_summary_below_cutoff_does_not_rule_out() -> None:
    text = summary(calculate(IdrsInput(25, MALE, 80.0, True, True, NONE)))
    assert "does not rule out diabetes" in text


inputs = st.builds(
    IdrsInput,
    age_years=st.integers(min_value=18, max_value=110),
    sex=st.sampled_from(Sex),
    waist_cm=st.floats(min_value=40.0, max_value=200.0, allow_nan=False),
    regular_exercise=st.booleans(),
    demanding_work=st.booleans(),
    family_history=st.sampled_from(FamilyHistory),
)


@given(inputs)
def test_score_always_valid_and_wording_always_safe(data: IdrsInput) -> None:
    result = calculate(data)
    assert 0 <= result.total <= MAX_SCORE
    assert result.total % 10 == 0
    text = summary(result).lower()
    assert "not a diagnosis" in text
    for phrase in FORBIDDEN:
        assert phrase not in text
