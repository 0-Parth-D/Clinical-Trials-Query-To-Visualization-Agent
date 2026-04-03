"""Committed example JSON files must match the public response contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.schemas import VisualizationResponse

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


@pytest.mark.parametrize(
    "path",
    sorted(EXAMPLES_DIR.glob("example_*.json")),
    ids=lambda p: p.name,
)
def test_example_file_parses_as_visualization_response(path: Path) -> None:
    raw = json.loads(path.read_text(encoding="utf-8"))
    VisualizationResponse.model_validate(raw)


def test_at_least_seven_examples_for_appendix_coverage() -> None:
    files = list(EXAMPLES_DIR.glob("example_*.json"))
    assert len(files) >= 7
