"""LLM-invalid chart types must coerce to a supported goal (schema integrity)."""

from __future__ import annotations

from app.intent.models import QueryIntent


def test_invalid_viz_goal_coerces_to_bar_chart() -> None:
    intent = QueryIntent.model_validate(
        {
            "filters": {},
            "viz_goal": "not_a_real_chart",
            "dimension_hint": "phase",
        }
    )
    assert intent.viz_goal == "bar_chart"
