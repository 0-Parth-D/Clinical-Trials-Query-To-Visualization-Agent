"""Heuristic intent: grouped bar vs country bar must not conflict."""

from __future__ import annotations

from app.intent.heuristic import _extract_vs_drugs, _wants_country_breakdown, interpret_heuristic
from app.schemas.request import QueryRequest


def test_compare_by_country_is_country_bar_not_grouped() -> None:
    intent = interpret_heuristic(
        QueryRequest(query="Compare trial counts by country for diabetes"),
    )
    assert intent.viz_goal == "bar_chart"
    assert intent.dimension_hint == "country"


def test_compare_by_country_short_phrase() -> None:
    intent = interpret_heuristic(QueryRequest(query="Compare by country"))
    assert intent.viz_goal == "bar_chart"
    assert intent.dimension_hint == "country"
    assert intent.comparison_drug is None


def test_country_overrides_stale_comparison_in_extra() -> None:
    intent = interpret_heuristic(
        QueryRequest(
            query="Compare by country for lung cancer",
            extra_filters={"comparison_drug": "nivolumab"},
        ),
    )
    assert intent.viz_goal == "bar_chart"
    assert intent.dimension_hint == "country"
    assert intent.comparison_drug is None


def test_country_overrides_drug_pair_when_query_asks_by_country() -> None:
    intent = interpret_heuristic(
        QueryRequest(
            query="Compare pembrolizumab vs nivolumab by country",
            drug_name="pembrolizumab",
            extra_filters={"comparison_drug": "nivolumab"},
        ),
    )
    assert intent.viz_goal == "bar_chart"
    assert intent.dimension_hint == "country"


def test_grouped_bar_from_vs_extracts_both_drugs() -> None:
    intent = interpret_heuristic(
        QueryRequest(query="lung cancer pembrolizumab vs nivolumab by phase"),
    )
    assert intent.viz_goal == "grouped_bar_chart"
    assert intent.comparison_drug == "nivolumab"
    assert intent.filters.get("drug_name") == "pembrolizumab"


def test_grouped_bar_form_pair() -> None:
    intent = interpret_heuristic(
        QueryRequest(
            query="diabetes trials by phase",
            drug_name="pembrolizumab",
            extra_filters={"comparison_drug": "nivolumab"},
        ),
    )
    assert intent.viz_goal == "grouped_bar_chart"
    assert intent.comparison_drug == "nivolumab"


def test_wants_country_breakdown_phrases() -> None:
    assert _wants_country_breakdown("trials per country for asthma")
    assert _wants_country_breakdown("geographic breakdown")
    assert _wants_country_breakdown("trial counts by country")
    assert not _wants_country_breakdown("pembrolizumab vs nivolumab")
    assert not _wants_country_breakdown("pembrolizumab vs nivolumab in european countries")


def test_extract_vs_drugs() -> None:
    a, b = _extract_vs_drugs("Compare pembrolizumab vs nivolumab for NSCLC")
    assert a == "pembrolizumab"
    assert b == "nivolumab"
