from pathlib import Path

import pytest

from dhadkan.analytics.nfhs import ENTITIES
from dhadkan.analytics.validation import read_rows, validate_rows

CSV = Path(__file__).parent.parent / "data" / "processed" / "nfhs6_indicators.csv"


@pytest.mark.skipif(not CSV.exists(), reason="processed CSV not generated yet")
def test_committed_dataset_is_complete_and_consistent() -> None:
    rows = read_rows(CSV)
    assert {r.state for r in rows} == set(ENTITIES)
    assert len(rows) == len(ENTITIES) * 12
    assert validate_rows(rows) == []
