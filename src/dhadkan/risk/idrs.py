"""Indian Diabetes Risk Score (IDRS), transcribed from Table 1 of source S6.

S6: Mohan V, Deepa R, Deepa M, Somannavar S, Datta M. A simplified Indian
Diabetes Risk Score for screening for undiagnosed diabetic subjects.
J Assoc Physicians India 2005;53:759-63.

A screening aid for undiagnosed diabetes. Not a diagnosis, and not a heart
attack predictor.
"""

from dataclasses import dataclass
from enum import StrEnum

MAX_SCORE = 100
# S6 abstract: an IDRS value of 60 or more had the optimum sensitivity and
# specificity.
SCREENING_CUTOFF = 60
# S6 abstract and Table 2: share of people scoring 60 or more who had
# undiagnosed diabetes in the Chennai study (positive predictive value).
STUDY_PPV_PERCENT = 17.0

# Input limits are design choices of this project, not taken from S6.
MIN_AGE = 18
MAX_AGE = 110
MIN_WAIST_CM = 40.0
MAX_WAIST_CM = 200.0

LIMITS_NOTE = (
    "This is a screening aid, not a diagnosis. It looks at diabetes risk only, "
    "not heart attack risk. It was developed in a Chennai study; in that study "
    f"about {STUDY_PPV_PERCENT:.0f}% of people scoring {SCREENING_CUTOFF} or more "
    "had undiagnosed diabetes."
)


class Sex(StrEnum):
    FEMALE = "female"
    MALE = "male"


class FamilyHistory(StrEnum):
    NONE = "none"
    ONE_PARENT = "one_parent"
    BOTH_PARENTS = "both_parents"


# S6 Table 1: waist (cm) at which 10 points and 20 points start, by sex.
WAIST_STEPS: dict[Sex, tuple[float, float]] = {
    Sex.FEMALE: (80.0, 90.0),
    Sex.MALE: (90.0, 100.0),
}

# S6 Table 1: family history of diabetes.
FAMILY_POINTS: dict[FamilyHistory, int] = {
    FamilyHistory.NONE: 0,
    FamilyHistory.ONE_PARENT: 10,
    FamilyHistory.BOTH_PARENTS: 20,
}


def age_points(age_years: int) -> int:
    if not MIN_AGE <= age_years <= MAX_AGE:
        raise ValueError(f"age must be between {MIN_AGE} and {MAX_AGE}")
    if age_years < 35:
        return 0
    if age_years < 50:
        return 20
    return 30


def waist_points(waist_cm: float, sex: Sex) -> int:
    if not MIN_WAIST_CM <= waist_cm <= MAX_WAIST_CM:
        raise ValueError(
            f"waist must be between {MIN_WAIST_CM:.0f} and {MAX_WAIST_CM:.0f} cm"
        )
    mid, high = WAIST_STEPS[sex]
    if waist_cm >= high:
        return 20
    if waist_cm >= mid:
        return 10
    return 0


def activity_points(regular_exercise: bool, demanding_work: bool) -> int:
    if regular_exercise and demanding_work:
        return 0
    if regular_exercise or demanding_work:
        return 20
    return 30


@dataclass(frozen=True)
class IdrsInput:
    age_years: int
    sex: Sex
    waist_cm: float
    regular_exercise: bool
    demanding_work: bool
    family_history: FamilyHistory


@dataclass(frozen=True)
class IdrsResult:
    age: int
    waist: int
    activity: int
    family: int

    @property
    def total(self) -> int:
        return self.age + self.waist + self.activity + self.family

    @property
    def at_or_above_cutoff(self) -> bool:
        return self.total >= SCREENING_CUTOFF


def calculate(data: IdrsInput) -> IdrsResult:
    return IdrsResult(
        age=age_points(data.age_years),
        waist=waist_points(data.waist_cm, data.sex),
        activity=activity_points(data.regular_exercise, data.demanding_work),
        family=FAMILY_POINTS[data.family_history],
    )


def summary(result: IdrsResult) -> str:
    score_line = f"Your score is {result.total} out of {MAX_SCORE}."
    if result.at_or_above_cutoff:
        advice = (
            f"This tool suggests considering a blood sugar screening test at "
            f"{SCREENING_CUTOFF} or above. Consider talking to a doctor "
            "about screening."
        )
    else:
        advice = (
            f"This is below the {SCREENING_CUTOFF} level this tool uses. That "
            "does not rule out diabetes; if you have symptoms or concerns, "
            "talk to a doctor."
        )
    return f"{score_line} {advice} {LIMITS_NOTE}"
