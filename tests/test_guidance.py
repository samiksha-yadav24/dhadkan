from typing import Any

from hypothesis import given
from hypothesis import strategies as st

from dhadkan.engine.guidance import (
    DISCLAIMER,
    DRAFT_NOTICE,
    build_banner,
    build_guidance,
    render_text,
)
from dhadkan.loader import Content
from dhadkan.models import EmergencyNumbers, Protocol

NUMBERS = EmergencyNumbers.model_validate(
    {
        "numbers": [
            {"number": "112", "label": "National emergency", "source_id": "S3"},
            {"number": "108", "label": "Ambulance service", "source_id": "S2"},
        ]
    }
)

DRAFT = {"status": "draft", "version": "0.1.0"}
REVIEWED = {
    "status": "clinician_reviewed",
    "version": "1.0.0",
    "reviewer": "Dr. Test",
    "reviewed_on": "2026-11-01",
}


def make_protocol(
    texts: list[str],
    review: dict[str, Any] | None = None,
    condition: str | None = None,
) -> Protocol:
    return Protocol.model_validate(
        {
            "id": "generated",
            "title": "Generated",
            "summary": "Generated protocol",
            "steps": [
                {
                    "id": f"s{i}",
                    "kind": "action",
                    "text": t,
                    "condition": condition,
                    "source_refs": [{"source_id": "S1", "locator": "p.1"}],
                }
                for i, t in enumerate(texts)
            ],
            "review": review or DRAFT,
        }
    )


def test_banner_uses_first_listed_number() -> None:
    banner = build_banner(NUMBERS)
    assert banner.primary == "112"
    assert banner.others == ("108",)
    assert banner.text == "Call 112 now"


def test_render_starts_with_banner_and_ends_with_disclaimer() -> None:
    text = render_text(build_guidance(make_protocol(["Do the thing"]), NUMBERS))
    lines = text.splitlines()
    assert lines[0] == "*** Call 112 now ***"
    assert lines[-1] == DISCLAIMER


def test_draft_protocol_shows_notice() -> None:
    text = render_text(build_guidance(make_protocol(["Do the thing"]), NUMBERS))
    assert DRAFT_NOTICE in text


def test_reviewed_protocol_hides_notice() -> None:
    protocol = make_protocol(["Do the thing"], review=REVIEWED)
    assert DRAFT_NOTICE not in render_text(build_guidance(protocol, NUMBERS))


def test_condition_is_shown_with_step() -> None:
    protocol = make_protocol(["Do the thing"], condition="If no response")
    text = render_text(build_guidance(protocol, NUMBERS))
    assert "1. [If no response] Do the thing" in text


def test_real_content_always_leads_with_112(content: Content) -> None:
    assert content.emergency_numbers.numbers[0].number == "112"
    for protocol in content.protocols.values():
        text = render_text(build_guidance(protocol, content.emergency_numbers))
        assert text.splitlines()[0] == "*** Call 112 now ***"


@given(texts=st.lists(st.text(min_size=3, max_size=220), min_size=1, max_size=15))
def test_banner_survives_any_step_text(texts: list[str]) -> None:
    text = render_text(build_guidance(make_protocol(texts), NUMBERS))
    lines = text.splitlines()
    assert lines[0] == "*** Call 112 now ***"
    assert lines[-1] == DISCLAIMER
