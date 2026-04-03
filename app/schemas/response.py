"""Visualization API response contract."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class VizType(str, Enum):
    """Supported visualization families (matches assignment / README vocabulary)."""

    bar_chart = "bar_chart"
    grouped_bar_chart = "grouped_bar_chart"
    time_series = "time_series"
    scatter_plot = "scatter_plot"
    histogram = "histogram"
    network_graph = "network_graph"


class SourceMeta(BaseModel):
    """Provenance for aggregated numbers (populated from real API calls in later steps)."""

    name: str = Field(..., description="Human-readable data source name.")
    api: str = Field(..., description="API base URL or endpoint identifier used.")
    retrieved_at: datetime = Field(
        ...,
        description="ISO-8601 timestamp when data was retrieved.",
    )
    result_count: int = Field(
        ...,
        ge=0,
        description="Number of trials (or primary records) included in the aggregation.",
    )


class MetaBlock(BaseModel):
    """Execution context: filters applied, assumptions, and optional warnings."""

    units: str | None = Field(default=None, description="Unit of measure for y-axis or metrics.")
    sort: str | None = Field(default=None, description="Recommended sort for chart rows.")
    time_granularity: str | None = Field(
        default=None,
        description="Bucket size for time axes (e.g. year, quarter).",
    )
    group_by: str | None = Field(
        default=None,
        description="Primary grouping dimension when applicable.",
    )
    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Effective filters after merging NL and optional request fields.",
    )
    source: SourceMeta = Field(..., description="ClinicalTrials.gov (or stub) provenance.")
    assumptions: list[str] = Field(
        default_factory=list,
        description="Explicit counting or normalization assumptions.",
    )
    warnings: list[str] | None = Field(
        default=None,
        description="Non-fatal issues (truncation, missing fields, fallback chart type).",
    )


class VisualizationSpec(BaseModel):
    """A single visualization payload: type, channels, and tabular or graph-ready rows."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "bar_chart",
                    "title": "Trials by phase (static stub)",
                    "encoding": {"x": "phase", "y": "trial_count"},
                    "data": [
                        {"phase": "Phase 1", "trial_count": 12},
                        {"phase": "Phase 2", "trial_count": 28},
                        {"phase": "Phase 3", "trial_count": 19},
                    ],
                }
            ]
        }
    }

    type: VizType = Field(..., description="Chart or graph family.")
    title: str = Field(..., description="Chart title suitable for display.")
    encoding: dict[str, Any] = Field(
        ...,
        description="Channel map (e.g. x, y) or network keys (nodes, edges).",
    )
    data: list[dict[str, Any]] = Field(
        ...,
        description="Frontend-ready records; row shape depends on type.",
    )


class VisualizationResponse(BaseModel):
    """Top-level response: one visualization plus metadata."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "visualization": {
                        "type": "bar_chart",
                        "title": "Trials by phase (static stub)",
                        "encoding": {"x": "phase", "y": "trial_count"},
                        "data": [
                            {"phase": "Phase 1", "trial_count": 12},
                            {"phase": "Phase 2", "trial_count": 28},
                            {"phase": "Phase 3", "trial_count": 19},
                        ],
                    },
                    "meta": {
                        "units": "trials",
                        "sort": "phase",
                        "time_granularity": None,
                        "group_by": "phase",
                        "filters": {"condition": "diabetes", "note": "stub"},
                        "source": {
                            "name": "ClinicalTrials.gov",
                            "api": "https://clinicaltrials.gov/api/v2/studies (stub)",
                            "retrieved_at": "2026-04-03T12:00:00Z",
                            "result_count": 59,
                        },
                        "assumptions": [
                            "Stub response only; real counts will come from API aggregation."
                        ],
                        "warnings": None,
                    },
                }
            ]
        }
    }

    visualization: VisualizationSpec
    meta: MetaBlock
