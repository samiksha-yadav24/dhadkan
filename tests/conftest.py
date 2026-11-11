from pathlib import Path

import pytest

from dhadkan.loader import Content, load_content


@pytest.fixture(scope="session")
def content_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "content"


@pytest.fixture(scope="session")
def content(content_dir: Path) -> Content:
    return load_content(content_dir)
