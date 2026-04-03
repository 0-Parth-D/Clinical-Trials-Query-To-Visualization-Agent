"""Structured query intent produced by LLM or heuristics."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


ALLOWED_VIZ_GOALS = frozenset(
    {
        "bar_chart",
        "grouped_bar_chart",
        "time_series",
        "scatter_plot",
        "histogram",
        "network_graph",
    }
)


class QueryIntent(BaseModel):
    """What to fetch and how to visualize; numbers always come from deterministic aggregation."""

    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Normalized filters (condition, drug_name, recruiting_only, years, etc.).",
    )
    viz_goal: str = Field(
        ...,
        description=(
            "One of: bar_chart, grouped_bar_chart, time_series, scatter_plot, "
            "histogram, network_graph"
        ),
    )
    dimension_hint: str | None = Field(
        default=None,
        description="Primary breakdown: phase, year, country, sponsor, drug, etc.",
    )
    comparison_drug: str | None = Field(
        default=None,
        description="Second drug for A vs B comparisons when applicable.",
    )
    notes: str | None = Field(default=None, description="Short rationale for graders/logs.")

    @field_validator("viz_goal")
    @classmethod
    def coerce_viz_goal(cls, v: str) -> str:
        if v in ALLOWED_VIZ_GOALS:
            return v
        return "bar_chart"
