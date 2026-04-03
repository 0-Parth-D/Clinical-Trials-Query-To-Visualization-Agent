"""POST /v1/query request body."""

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class QueryRequest(BaseModel):
    """Natural-language query plus optional structured filters that override or tighten NL extraction."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "Show me diabetes trials by phase in the United States",
                    "condition": "diabetes",
                    "country": "United States",
                },
                {
                    "query": "Count pembrolizumab lung cancer trials by recruitment status",
                    "drug_name": "pembrolizumab",
                    "condition": "lung cancer",
                },
            ]
        }
    }

    query: str = Field(
        ...,
        description="Primary natural-language question (required).",
        min_length=1,
        examples=["Trials for breast cancer by phase since 2020"],
    )
    drug_name: str | None = Field(
        default=None,
        description="Optional drug or intervention name; tightens filters when set.",
    )
    condition: str | None = Field(
        default=None,
        description="Optional disease or condition label.",
    )
    trial_phase: str | None = Field(
        default=None,
        description="Optional trial phase filter (e.g. PHASE3, Phase 2).",
    )
    sponsor: str | None = Field(
        default=None,
        description="Optional sponsor or lead organization name.",
    )
    country: str | None = Field(
        default=None,
        description="Optional country for site or facility location filters.",
    )
    start_year: int | None = Field(
        default=None,
        description="Optional inclusive lower bound on trial start year.",
        ge=1900,
        le=2100,
    )
    end_year: int | None = Field(
        default=None,
        description="Optional inclusive upper bound on trial start year.",
        ge=1900,
        le=2100,
    )
    extra_filters: dict[str, Any] | None = Field(
        default=None,
        description="Reserved for forward-compatible structured filter key/values.",
    )

    @field_validator("query")
    @classmethod
    def query_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("query must be a non-empty string")
        return v.strip()

    @model_validator(mode="after")
    def year_order(self) -> "QueryRequest":
        if (
            self.start_year is not None
            and self.end_year is not None
            and self.start_year > self.end_year
        ):
            raise ValueError("start_year must be less than or equal to end_year")
        return self
