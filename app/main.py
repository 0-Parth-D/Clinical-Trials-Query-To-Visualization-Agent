"""ClinicalTrials.gov query-to-visualization API."""

from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI

from app.config import Settings
from app.ctgov import (
    build_query_term,
    effective_filters,
    fetch_studies,
    normalize_study,
)
from app.intent import interpret_intent
from app.schemas import QueryRequest, VisualizationResponse
from app.viz import build_visualization


@lru_cache
def get_settings() -> Settings:
    return Settings()


app = FastAPI(
    title="ClinicalTrials Query-to-Visualization Agent",
    version="0.2.0",
    description=(
        "Accepts natural language plus optional structured filters, fetches "
        "ClinicalTrials.gov v2 studies, and returns chart-ready JSON with deep citations."
    ),
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/v1/query",
    response_model=VisualizationResponse,
    tags=["query"],
    summary="Interpret query and return visualization spec",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "minimal": {
                            "summary": "NL only",
                            "value": {"query": "Breast cancer trials in Canada by phase"},
                        },
                        "structured": {
                            "summary": "NL plus filters",
                            "value": {
                                "query": "Trend of oncology trials",
                                "condition": "lung cancer",
                                "country": "Canada",
                                "start_year": 2018,
                                "end_year": 2024,
                            },
                        },
                    }
                }
            }
        }
    },
)
async def query_visualize(body: QueryRequest) -> VisualizationResponse:
    """
    Merge structured fields with LLM or heuristic intent, query ClinicalTrials.gov,
    aggregate deterministically, and return a visualization specification with citations.
    """
    settings = get_settings()
    intent = interpret_intent(body, settings)
    ef = effective_filters(body, intent)
    term = build_query_term(ef, intent)
    studies, warnings = await fetch_studies(term, settings)
    records = [normalize_study(s) for s in studies]
    return build_visualization(intent, ef, records, warnings, settings, term)
