import json
from pathlib import Path

from app.config import Settings
from app.ctgov.normalize import normalize_study
from app.ctgov.query_builder import EffectiveFilters
from app.intent.models import QueryIntent
from app.viz.engine import build_visualization


def _loadstudy() -> dict:
    return json.loads((Path(__file__).parent / "fixtures" / "min_study.json").read_text(encoding="utf-8"))


def test_phase_bar_has_citations() -> None:
    raw = _loadstudy()
    records = [normalize_study(raw)]
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
    intent = QueryIntent(viz_goal="bar_chart", dimension_hint="phase")
    resp = build_visualization(intent, ef, records, [], settings, "AREA[ConditionSearch]diabetes")
    assert resp.visualization.type.value == "bar_chart"
    assert resp.meta.source.result_count == 1
    row = resp.visualization.data[0]
    assert "citations" in row
    assert row["citations"][0]["nct_id"] == "NCT09999999"


def test_network_graph_shape() -> None:
    raw = _loadstudy()
    records = [normalize_study(raw)]
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
        raw_query="network",
    )
    intent = QueryIntent(viz_goal="network_graph")
    resp = build_visualization(intent, ef, records, [], settings, "diabetes")
    assert resp.visualization.data
    blob = resp.visualization.data[0]
    assert "nodes" in blob and "edges" in blob
    assert any(n["kind"] == "sponsor" for n in blob["nodes"])
