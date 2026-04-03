"""Deep citations: excerpts must be traceable to normalized trial text (bonus integrity)."""

from __future__ import annotations

import json
from pathlib import Path

from app.config import Settings
from app.ctgov.normalize import normalize_study
from app.ctgov.query_builder import EffectiveFilters
from app.intent.models import QueryIntent
from app.viz.engine import build_visualization


def _fixture_study() -> dict:
    p = Path(__file__).parent / "fixtures" / "min_study.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_bar_citation_excerpt_is_prefix_of_source_text() -> None:
    raw = _fixture_study()
    record = normalize_study(raw)
    settings = Settings()
    ef = EffectiveFilters(
        condition="diabetes",
        drug_name=None,
        comparison_drug=None,
        sponsor=None,
        country=None,
        trial_phase=None,
        start_year=None,
        end_year=None,
        recruiting_only=False,
        raw_query="test",
    )
    resp = build_visualization(
        QueryIntent(viz_goal="bar_chart", dimension_hint="phase"),
        ef,
        [record],
        [],
        settings,
        "AREA[ConditionSearch]diabetes",
    )
    ex = resp.visualization.data[0]["citations"][0]["excerpt"]
    source = record.raw_excerpt_source or record.brief_title
    assert source.startswith(ex) or ex == source
