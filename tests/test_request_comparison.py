"""Top-level comparison_drug on QueryRequest must be honored."""

from __future__ import annotations

from app.ctgov.query_builder import effective_filters, build_query_term
from app.intent.models import QueryIntent
from app.schemas.request import QueryRequest, request_comparison_drug


def test_request_comparison_prefers_top_level_over_extra() -> None:
    body = QueryRequest(
        query="trials",
        comparison_drug="nivolumab",
        extra_filters={"comparison_drug": "atezolizumab"},
    )
    assert request_comparison_drug(body) == "nivolumab"


def test_effective_filters_top_level_comparison_only() -> None:
    body = QueryRequest(
        query="lung cancer trials by phase",
        drug_name="pembrolizumab",
        comparison_drug="nivolumab",
    )
    intent = QueryIntent(filters={}, viz_goal="bar_chart", dimension_hint="phase")
    ef = effective_filters(body, intent)
    assert ef.drug_name == "pembrolizumab"
    assert ef.comparison_drug == "nivolumab"


def test_query_term_or_with_top_level_comparison_only() -> None:
    from app.ctgov.query_builder import EffectiveFilters

    ef = EffectiveFilters(
        condition=None,
        drug_name="pembrolizumab",
        comparison_drug="nivolumab",
        sponsor=None,
        country=None,
        trial_phase=None,
        start_year=None,
        end_year=None,
        recruiting_only=False,
        raw_query="q",
    )
    intent = QueryIntent(filters={}, viz_goal="bar_chart", dimension_hint="phase")
    term = build_query_term(ef, intent)
    assert "OR" in term and "nivolumab" in term
