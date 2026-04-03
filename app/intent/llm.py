"""OpenAI structured intent extraction."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from app.config import Settings
from app.intent.models import QueryIntent
from app.schemas.request import QueryRequest

logger = logging.getLogger(__name__)

VIZ_ENUM = [
    "bar_chart",
    "grouped_bar_chart",
    "time_series",
    "scatter_plot",
    "histogram",
    "network_graph",
]


def interpret_llm(body: QueryRequest, settings: Settings) -> QueryIntent | None:
    key = settings.openai_api_key
    if not key or not key.strip():
        return None

    req_dump = body.model_dump(exclude_none=True)
    system = (
        "You convert clinical-trials questions into a single JSON object with keys: "
        "filters (object: optional keys condition, drug_name, sponsor, country, "
        "trial_phase, start_year, end_year, recruiting_only boolean), "
        f"viz_goal (one of {VIZ_ENUM}), dimension_hint (string or null), "
        "comparison_drug (string or null), notes (string or null). "
        "Never invent trial counts. If comparing two drugs, set comparison_drug."
    )
    user = f"Request JSON:\n{json.dumps(req_dump, ensure_ascii=False, indent=2)}"

    kwargs: dict[str, Any] = {}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url

    try:
        client = OpenAI(api_key=key, **kwargs)
        completion = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content
        if not raw:
            return None
        data = json.loads(raw)
        return QueryIntent.model_validate(data)
    except Exception as e:
        logger.warning("LLM intent failed: %s", e)
        return None
