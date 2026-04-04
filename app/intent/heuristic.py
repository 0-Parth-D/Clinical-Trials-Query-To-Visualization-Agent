"""Rule-based intent when no LLM is configured or API fails."""

from __future__ import annotations

import re

from app.intent.models import QueryIntent
from app.schemas.request import QueryRequest, request_comparison_drug

GOALS = (
    "bar_chart",
    "grouped_bar_chart",
    "time_series",
    "scatter_plot",
    "histogram",
    "network_graph",
)


def _extract_vs_drugs(query: str) -> tuple[str | None, str | None]:
    """
    Parse primary and comparison intervention from 'A vs B' / 'A versus B'.
    Used so grouped_bar_chart gets drug_name + comparison_drug without relying on form fields only.
    """
    parts = re.split(r"\bvs\.?\b|\bversus\b", query, maxsplit=1, flags=re.I)
    if len(parts) != 2:
        return None, None
    left = parts[0].strip()
    right = parts[1].strip()
    # Comparison: strip trailing context ("nivolumab for lung cancer" -> nivolumab)
    right_main = re.split(r"\s+(?:for|in|by|with|and|,)\s+", right, maxsplit=1)[0].strip()
    comparison = right_main[:120] if right_main else None

    left_clean = re.sub(
        r"(?i)^\s*(compare|comparing|show|give me|find|trials?|trials?\s+for)\s+",
        "",
        left,
    ).strip()
    left_clean = re.sub(r"(?i)\s+(trials?|studies?)\s*$", "", left_clean).strip()
    primary = None
    if left_clean:
        tokens = [t for t in re.split(r"[\s,]+", left_clean) if len(t) >= 2]
        if tokens:
            primary = tokens[-1][:120]
    return primary, comparison


def _wants_country_breakdown(q: str) -> bool:
    """True when the question asks for a per-country split (not merely filtering to one country)."""
    if re.search(r"\b(by|per|across)\s+(?:country|countries)\b", q):
        return True
    # "A vs B in multiple countries" should stay drug-comparison, not country bars.
    if (
        "geographic" in q or re.search(r"\bcountries\b", q)
    ) and not re.search(r"\bvs\.?\b|\bversus\b", q):
        return True
    if re.search(r"\bcountry\b", q) and not re.search(r"\bvs\.?\b|\bversus\b", q):
        return True
    return False


def merge_country_breakdown_request(body: QueryRequest, intent: QueryIntent) -> QueryIntent:
    """
    Phrases like 'compare by country' must win over grouped-bar or a stale comparison_drug
    in extra_filters; otherwise users see one phase bucket or the wrong chart.
    """
    if not _wants_country_breakdown(body.query.lower()):
        return intent
    return intent.model_copy(
        update={
            "viz_goal": "bar_chart",
            "dimension_hint": "country",
            "comparison_drug": None,
        },
    )


def promote_structured_pair_to_grouped(body: QueryRequest, intent: QueryIntent) -> QueryIntent:
    """
    Form fields drug_name + extra_filters.comparison_drug imply a two-drug comparison.
    Without this, an LLM may return bar_chart and build_query_term would only search the
    primary intervention.
    """
    if _wants_country_breakdown(body.query.lower()):
        return intent
    drug = body.drug_name and str(body.drug_name).strip()
    if not drug:
        return intent
    cmp = request_comparison_drug(body)
    if not cmp:
        return intent
    return intent.model_copy(
        update={
            "viz_goal": "grouped_bar_chart",
            "dimension_hint": "phase",
            "comparison_drug": cmp,
        },
    )


def interpret_heuristic(body: QueryRequest) -> QueryIntent:
    q = body.query.lower()
    filters: dict = {}
    if body.condition:
        filters["condition"] = body.condition
    if body.drug_name:
        filters["drug_name"] = body.drug_name
    if body.sponsor:
        filters["sponsor"] = body.sponsor
    if body.country:
        filters["country"] = body.country
    if body.trial_phase:
        filters["trial_phase"] = body.trial_phase
    if body.start_year is not None:
        filters["start_year"] = body.start_year
    if body.end_year is not None:
        filters["end_year"] = body.end_year

    if "recruit" in q:
        filters["recruiting_only"] = True

    has_vs = bool(re.search(r"\bvs\.?\b|\bversus\b", body.query, flags=re.I))
    pair_from_form = bool(
        body.drug_name and str(body.drug_name).strip() and request_comparison_drug(body),
    )

    viz = "bar_chart"
    dim: str | None = "phase"
    comparison: str | None = None

    if "network" in q or ("graph" in q and "scatter" not in q):
        viz = "network_graph"
        dim = None
    elif "scatter" in q or ("enrollment" in q and "year" in q):
        viz = "scatter_plot"
        dim = "enrollment_vs_year"
    elif "trend" in q or "over time" in q or "per year" in q or "each year" in q or "since" in q:
        viz = "time_series"
        dim = "year"
    elif "histogram" in q or ("distribution" in q and "phase" not in q):
        viz = "histogram"
        dim = "start_year"
    elif has_vs or pair_from_form:
        # Grouped bar: do not use bare "compare" — it conflicts with "compare/country breakdown".
        viz = "grouped_bar_chart"
        dim = "phase"
        if pair_from_form:
            comparison = request_comparison_drug(body)
        if has_vs:
            primary, comp_vs = _extract_vs_drugs(body.query)
            if comp_vs:
                comparison = comp_vs
            if primary and not (body.drug_name and str(body.drug_name).strip()):
                filters["drug_name"] = primary

    # Grouped bar from form: need both drugs (comparison alone must not steal country intent).
    cmp_req = request_comparison_drug(body)
    if (
        cmp_req
        and viz != "grouped_bar_chart"
        and body.drug_name
        and str(body.drug_name).strip()
    ):
        comparison = cmp_req
        viz = "grouped_bar_chart"
        dim = "phase"

    return merge_country_breakdown_request(
        body,
        QueryIntent(
            filters=filters,
            viz_goal=viz if viz in GOALS else "bar_chart",
            dimension_hint=dim,
            comparison_drug=comparison,
            notes="Heuristic intent (no LLM or LLM unavailable).",
        ),
    )
