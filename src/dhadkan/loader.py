"""Load content from YAML, validate it, and check cross-references."""

from dataclasses import dataclass
from pathlib import Path

import yaml

from dhadkan.models import EmergencyNumbers, Protocol, Source, SourceFile


class ContentError(Exception):
    """Content failed a safety check."""


@dataclass(frozen=True)
class Content:
    sources: dict[str, Source]
    emergency_numbers: EmergencyNumbers
    protocols: dict[str, Protocol]


def _read(path: Path) -> object:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_content(content_dir: Path) -> Content:
    source_file = SourceFile.model_validate(_read(content_dir / "sources.yaml"))
    sources = {s.id: s for s in source_file.sources}

    numbers = EmergencyNumbers.model_validate(
        _read(content_dir / "emergency_numbers.yaml")
    )
    for n in numbers.numbers:
        if n.source_id not in sources:
            raise ContentError(f"emergency number {n.number}: unknown {n.source_id}")

    protocols: dict[str, Protocol] = {}
    for path in sorted((content_dir / "protocols").glob("*.yaml")):
        protocol = Protocol.model_validate(_read(path))
        for step in protocol.steps:
            for ref in step.source_refs:
                if ref.source_id not in sources:
                    raise ContentError(
                        f"{path.name}: step '{step.id}' cites unknown {ref.source_id}"
                    )
        protocols[protocol.id] = protocol

    return Content(sources=sources, emergency_numbers=numbers, protocols=protocols)
