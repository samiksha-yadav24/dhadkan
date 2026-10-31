from datetime import date
from typing import Any

import pytest
from pydantic import ValidationError

from dhadkan.models import Protocol, Review, Source, SourceFile

REF = {"source_id": "S2", "locator": "p.85"}


def step(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "check-response",
        "kind": "check",
        "text": "Tap the shoulder and ask loudly if they are alright.",
        "source_refs": [REF],
    }
    return {**base, **over}


def protocol(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "test-protocol",
        "title": "Test",
        "summary": "A test protocol.",
        "steps": [step()],
        "review": {"status": "draft", "version": "0.1.0"},
    }
    return {**base, **over}


def test_valid_protocol_passes() -> None:
    assert Protocol.model_validate(protocol()).id == "test-protocol"


def test_step_without_source_fails() -> None:
    with pytest.raises(ValidationError):
        Protocol.model_validate(protocol(steps=[step(source_refs=[])]))


def test_step_missing_source_key_fails() -> None:
    bad = step()
    del bad["source_refs"]
    with pytest.raises(ValidationError):
        Protocol.model_validate(protocol(steps=[bad]))


def test_missing_review_fails() -> None:
    bad = protocol()
    del bad["review"]
    with pytest.raises(ValidationError):
        Protocol.model_validate(bad)


def test_reviewed_without_reviewer_fails() -> None:
    with pytest.raises(ValidationError):
        Review.model_validate({"status": "clinician_reviewed", "version": "1.0.0"})


def test_reviewed_with_reviewer_passes() -> None:
    r = Review.model_validate(
        {
            "status": "clinician_reviewed",
            "version": "1.0.0",
            "reviewer": "Dr. Example",
            "reviewed_on": date(2026, 11, 1),
        }
    )
    assert r.reviewer == "Dr. Example"


def test_duplicate_step_ids_fail() -> None:
    with pytest.raises(ValidationError):
        Protocol.model_validate(protocol(steps=[step(), step()]))


def test_unknown_key_rejected() -> None:
    with pytest.raises(ValidationError):
        Protocol.model_validate(protocol(surprise="x"))


def test_source_needs_year_or_note() -> None:
    base = {
        "id": "S9",
        "title": "Some doc",
        "publisher": "Someone",
        "role": "secondary",
        "accessed": date(2026, 10, 24),
    }
    with pytest.raises(ValidationError):
        Source.model_validate(base)
    assert Source.model_validate({**base, "year_note": "not printed"}).year is None


def test_duplicate_source_ids_fail() -> None:
    s = {
        "id": "S1",
        "title": "Doc",
        "publisher": "Pub",
        "role": "primary",
        "accessed": date(2026, 10, 24),
        "year": 2017,
    }
    with pytest.raises(ValidationError):
        SourceFile.model_validate({"sources": [s, s]})
