import json
from pathlib import Path

from dhadkan.engine.bundle import build_bundle, write_bundle
from dhadkan.loader import Content


def test_bundle_has_banner_and_protocols(content: Content) -> None:
    bundle = build_bundle(content)
    assert bundle["banner"]["primary"] == "112"
    assert "cardiac-arrest-cols" in bundle["protocols"]
    assert len(bundle["content_hash"]) == 64


def test_bundle_is_deterministic(content: Content) -> None:
    first = build_bundle(content)["content_hash"]
    second = build_bundle(content)["content_hash"]
    assert first == second


def test_written_file_round_trips(content: Content, tmp_path: Path) -> None:
    out = tmp_path / "nested" / "bundle.json"
    write_bundle(content, out)
    assert json.loads(out.read_text(encoding="utf-8")) == build_bundle(content)


def test_hash_changes_when_content_changes(content: Content) -> None:
    changed = Content(
        sources=content.sources,
        emergency_numbers=content.emergency_numbers,
        protocols={},
    )
    original_hash = build_bundle(content)["content_hash"]
    changed_hash = build_bundle(changed)["content_hash"]
    assert changed_hash != original_hash
