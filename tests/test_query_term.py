"""ClinicalTrials.gov query.term composition."""

from __future__ import annotations

from app.ctgov.query_builder import EffectiveFilters, build_query_term
from app.intent.heuristic import merge_country_breakdown_request, promote_structured_pair_to_grouped
from app.intent.models import QueryIntent
from app.schemas.request import QueryRequest


def _ef(**overrides: object) -> EffectiveFilters:
    base: dict[str, object] = {
        "condition": None,
        "drug_name": None,
        "comparison_drug": None,
        "sponsor": None,
        "country": None,
        "trial_phase": None,
        "start_year": None,
        "end_year": None,
        "recruiting_only": False,
        "raw_query": "test",
    }
    base.update(overrides)
    return EffectiveFilters(**base)  # type: ignore[arg-type]


def test_or_intervention_when_both_drugs_even_if_intent_bar_chart() -> None:
    ef = _ef(drug_name="pembrolizumab", comparison_drug="nivolumab")
    intent = QueryIntent(filters={}, viz_goal="bar_chart", dimension_hint="phase")
    term = build_query_term(ef, intent)
    assert "OR" in term
    assert "pembrolizumab" in term
    assert "nivolumab" in term


def test_promote_llm_bar_to_grouped_when_form_has_pair() -> None:
    body = QueryRequest(
        query="Show phase counts for lung cancer",
        drug_name="pembrolizumab",
        extra_filters={"comparison_drug": "nivolumab"},
    )
    intent = QueryIntent(filters={}, viz_goal="bar_chart", dimension_hint="phase")
    out = promote_structured_pair_to_grouped(body, intent)
    assert out.viz_goal == "grouped_bar_chart"
    assert out.comparison_drug == "nivolumab"


def test_promote_skipped_when_country_breakdown_in_query() -> None:
    body = QueryRequest(
        query="Trials by country",
        drug_name="pembrolizumab",
        extra_filters={"comparison_drug": "nivolumab"},
    )
    intent = QueryIntent(filters={}, viz_goal="bar_chart", dimension_hint="phase")
    out = promote_structured_pair_to_grouped(body, intent)
    assert out.viz_goal == "bar_chart"


def test_country_merge_wins_over_form_pair() -> None:
    body = QueryRequest(
        query="Compare by country",
        drug_name="pembrolizumab",
        extra_filters={"comparison_drug": "nivolumab"},
    )
    intent = QueryIntent(filters={}, viz_goal="bar_chart", dimension_hint="phase")
    promoted = promote_structured_pair_to_grouped(body, intent)
    merged = merge_country_breakdown_request(body, promoted)
    assert merged.viz_goal == "bar_chart"
    assert merged.dimension_hint == "country"
    assert merged.comparison_drug is None
