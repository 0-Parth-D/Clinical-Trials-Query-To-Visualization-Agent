"""effective_filters must honor extra_filters (e.g. comparison_drug from the UI)."""

from __future__ import annotations

from app.ctgov.query_builder import effective_filters
from app.intent.models import QueryIntent
from app.schemas.request import QueryRequest


def test_comparison_drug_from_extra_filters_overrides_missing_intent() -> None:
    body = QueryRequest(
        query="compare drugs by phase",
        drug_name="pembrolizumab",
        extra_filters={"comparison_drug": "nivolumab"},
    )
    intent = QueryIntent(
        filters={},
        viz_goal="grouped_bar_chart",
        dimension_hint="phase",
        comparison_drug=None,
    )
    ef = effective_filters(body, intent)
    assert ef.drug_name == "pembrolizumab"
    assert ef.comparison_drug == "nivolumab"


def test_comparison_drug_from_extra_when_llm_omits() -> None:
    body = QueryRequest(
        query="lung cancer trials",
        drug_name="DrugA",
        extra_filters={"comparison_drug": "DrugB"},
    )
    intent = QueryIntent(
        filters={"drug_name": "ignored_when_body_set"},
        viz_goal="grouped_bar_chart",
        comparison_drug=None,
    )
    ef = effective_filters(body, intent)
    assert ef.drug_name == "DrugA"
    assert ef.comparison_drug == "DrugB"


def test_drug_name_fallback_from_extra_filters() -> None:
    body = QueryRequest(
        query="trials by phase",
        extra_filters={"drug_name": "aspirin", "comparison_drug": "placebo"},
    )
    intent = QueryIntent(
        filters={},
        viz_goal="grouped_bar_chart",
        comparison_drug=None,
    )
    ef = effective_filters(body, intent)
    assert ef.drug_name == "aspirin"
    assert ef.comparison_drug == "placebo"


def test_country_bar_intent_drops_comparison_from_extra() -> None:
    body = QueryRequest(
        query="diabetes by country",
        extra_filters={"comparison_drug": "nivolumab"},
    )
    intent = QueryIntent(
        filters={},
        viz_goal="bar_chart",
        dimension_hint="country",
        comparison_drug=None,
    )
    ef = effective_filters(body, intent)
    assert ef.comparison_drug is None
