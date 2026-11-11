"""Compile validated content into one JSON bundle for the offline app."""

import hashlib
import json
from pathlib import Path
from typing import Any

from dhadkan.engine.guidance import DISCLAIMER, build_banner
from dhadkan.loader import Content

SCHEMA_VERSION = 1


def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False)


def build_bundle(content: Content) -> dict[str, Any]:
    banner = build_banner(content.emergency_numbers)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "banner": {
            "text": banner.text,
            "primary": banner.primary,
            "others": list(banner.others),
        },
        "disclaimer": DISCLAIMER,
        "emergency_numbers": content.emergency_numbers.model_dump(mode="json"),
        "sources": {k: v.model_dump(mode="json") for k, v in content.sources.items()},
        "protocols": {
            k: v.model_dump(mode="json") for k, v in content.protocols.items()
        },
    }
    payload["content_hash"] = hashlib.sha256(_dump(payload).encode("utf-8")).hexdigest()
    return payload


def write_bundle(content: Content, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_dump(build_bundle(content)) + "\n", encoding="utf-8")
