from pathlib import Path

import pytest

from dhadkan.loader import ContentError, load_content

CONTENT = Path(__file__).resolve().parent.parent / "content"


def test_real_content_is_valid() -> None:
    content = load_content(CONTENT)
    assert "cardiac-arrest-cols" in content.protocols


def test_every_step_has_a_known_source() -> None:
    content = load_content(CONTENT)
    for protocol in content.protocols.values():
        for step in protocol.steps:
            assert step.source_refs
            for ref in step.source_refs:
                assert ref.source_id in content.sources


def test_112_is_listed_with_a_source() -> None:
    content = load_content(CONTENT)
    numbers = {n.number: n for n in content.emergency_numbers.numbers}
    assert "112" in numbers
    assert numbers["112"].source_id in content.sources


def test_unknown_source_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "protocols").mkdir()
    (tmp_path / "sources.yaml").write_text(
        "sources:\n  - {id: S1, title: Doc, publisher: Pub, role: primary,"
        " year: 2017, accessed: 2026-10-29}\n",
        encoding="utf-8",
    )
    (tmp_path / "emergency_numbers.yaml").write_text(
        "numbers:\n  - {number: '108', label: Ambulance, source_id: S1}\n",
        encoding="utf-8",
    )
    (tmp_path / "protocols" / "p.yaml").write_text(
        "id: p\ntitle: Test\nsummary: Test protocol\nsteps:\n"
        "  - id: a\n    kind: action\n    text: Do the thing\n"
        "    source_refs: [{source_id: S9, locator: p.1}]\n"
        "review: {status: draft, version: '0.1.0'}\n",
        encoding="utf-8",
    )
    with pytest.raises(ContentError):
        load_content(tmp_path)
