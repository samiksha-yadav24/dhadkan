"""Content schemas: the safety gate for all medical content."""

from datetime import date
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

SourceId = Annotated[str, StringConstraints(pattern=r"^S\d+$")]
Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceRole(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


class Source(_Strict):
    id: SourceId
    title: str = Field(min_length=3)
    publisher: str = Field(min_length=2)
    role: SourceRole
    accessed: date
    year: int | None = Field(default=None, ge=1990, le=2100)
    year_note: str | None = None
    url: str | None = None

    @model_validator(mode="after")
    def year_or_note(self) -> Self:
        if self.year is None and not self.year_note:
            raise ValueError("source needs a year, or a year_note saying why not")
        return self


class SourceFile(_Strict):
    sources: list[Source] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ids(self) -> Self:
        ids = [s.id for s in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate source ids")
        return self


class SourceRef(_Strict):
    source_id: SourceId
    locator: str = Field(min_length=1, description="page, section or figure")


class StepKind(StrEnum):
    CHECK = "check"
    ACTION = "action"
    WARNING = "warning"


class Step(_Strict):
    id: Slug
    kind: StepKind
    text: str = Field(min_length=3, max_length=220)
    condition: str | None = None
    source_refs: list[SourceRef] = Field(min_length=1)


class ReviewStatus(StrEnum):
    DRAFT = "draft"
    CLINICIAN_REVIEWED = "clinician_reviewed"


class Review(_Strict):
    status: ReviewStatus
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    reviewer: str | None = None
    reviewed_on: date | None = None
    open_questions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def reviewed_needs_reviewer(self) -> Self:
        if self.status is ReviewStatus.CLINICIAN_REVIEWED and not (
            self.reviewer and self.reviewed_on
        ):
            raise ValueError("clinician_reviewed requires reviewer and reviewed_on")
        return self


class Protocol(_Strict):
    id: Slug
    title: str = Field(min_length=3)
    summary: str = Field(min_length=3)
    language: Literal["en", "hi", "mr"] = "en"
    steps: list[Step] = Field(min_length=1)
    review: Review

    @model_validator(mode="after")
    def unique_step_ids(self) -> Self:
        ids = [s.id for s in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate step ids")
        return self


class EmergencyNumber(_Strict):
    number: str = Field(pattern=r"^\d{3,4}$")
    label: str = Field(min_length=3)
    source_id: SourceId


class EmergencyNumbers(_Strict):
    numbers: list[EmergencyNumber] = Field(min_length=1)
