"""Rule-based intent when no LLM is configured or API fails."""

from __future__ import annotations

import re

from app.intent.models import QueryIntent
from app.schemas.request import QueryRequest

GOALS = (
    "bar_chart",
    "grouped_bar_chart",
    "time_series",
    "scatter_plot",
    "histogram",
    "network_graph",
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

    viz = "bar_chart"
    dim: str | None = "phase"
    comparison: str | None = None

    if "network" in q or "graph" in q and "scatter" not in q:
        viz = "network_graph"
        dim = None
    elif "scatter" in q or ("enrollment" in q and "year" in q):
        viz = "scatter_plot"
        dim = "enrollment_vs_year"
    elif "trend" in q or "over time" in q or "per year" in q or "each year" in q or "since" in q:
        viz = "time_series"
        dim = "year"
    elif "histogram" in q or "distribution" in q and "phase" not in q:
        viz = "histogram"
        dim = "start_year"
    elif re.search(r"\bvs\.?\b|\bcompare\b|\bversus\b", q):
        viz = "grouped_bar_chart"
        dim = "phase"
        parts = re.split(r"\bvs\.?\b|\bversus\b", body.query, maxsplit=1, flags=re.I)
        if len(parts) == 2:
            right = parts[1].strip()
            comparison = right.split(",")[0].strip()[:120] or None

    if isinstance(body.extra_filters, dict):
        alt = body.extra_filters.get("comparison_drug")
        if isinstance(alt, str) and alt.strip():
            comparison = alt.strip()
            viz = "grouped_bar_chart"

    if "country" in q or "geographic" in q or "countries" in q or body.country:
        if viz == "bar_chart":
            dim = "country"

    return QueryIntent(
        filters=filters,
        viz_goal=viz if viz in GOALS else "bar_chart",
        dimension_hint=dim,
        comparison_drug=comparison,
        notes="Heuristic intent (no LLM or LLM unavailable).",
    )
