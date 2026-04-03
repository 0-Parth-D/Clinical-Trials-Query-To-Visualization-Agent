"""Aggregated counts must be recomputable from the same normalized records (anti-hallucination)."""

from __future__ import annotations

import json
from pathlib import Path

from app.config import Settings
from app.ctgov.normalize import normalize_study
from app.ctgov.query_builder import EffectiveFilters
from app.intent.models import QueryIntent
from app.viz.engine import build_visualization


def _rec(path: str) -> list:
    p = Path(__file__).parent / path
    return [normalize_study(json.loads(p.read_text(encoding="utf-8")))]


def test_phase_bar_trial_count_matches_manual_bucket() -> None:
    records = _rec("fixtures/min_study.json")
    settings = Settings()
    ef = EffectiveFilters(
        condition=None,
        drug_name=None,
        comparison_drug=None,
        sponsor=None,
        country=None,
        trial_phase=None,
        start_year=None,
        end_year=None,
        recruiting_only=False,
        raw_query="x",
    )
    resp = build_visualization(
        QueryIntent(viz_goal="bar_chart", dimension_hint="phase"),
        ef,
        records,
        [],
        settings,
        "test",
    )
    phase_rows = {r["phase"]: r["trial_count"] for r in resp.visualization.data}
    assert phase_rows.get("Phase 2") == 1
    assert sum(phase_rows.values()) == len(records[0].phases)


def test_time_series_year_buckets_sum_to_trial_rows_not_double_count_across_years() -> None:
    records = _rec("fixtures/min_study.json")
    settings = Settings()
    ef = EffectiveFilters(
        condition=None,
        drug_name=None,
        comparison_drug=None,
        sponsor=None,
        country=None,
        trial_phase=None,
        start_year=None,
        end_year=None,
        recruiting_only=False,
        raw_query="x",
    )
    resp = build_visualization(
        QueryIntent(viz_goal="time_series", dimension_hint="year"),
        ef,
        records,
        [],
        settings,
        "test",
    )
    counts = [row["trial_count"] for row in resp.visualization.data if row["year"] != "Unknown"]
    assert sum(counts) == 1
