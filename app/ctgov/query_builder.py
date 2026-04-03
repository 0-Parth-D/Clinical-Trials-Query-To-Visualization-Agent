"""Build ClinicalTrials.gov v2 `query.term` and merge request + intent filters."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.intent.models import QueryIntent
from app.schemas.request import QueryRequest


def _q(s: str) -> str:
    return " ".join(s.split())


def _area(field: str, value: str) -> str:
    v = _q(value)
    return f"AREA[{field}]{v}" if v else ""


@dataclass
class EffectiveFilters:
    """Filters after merging optional request fields with LLM/heuristic intent."""

    condition: str | None
    drug_name: str | None
    comparison_drug: str | None
    sponsor: str | None
    country: str | None
    trial_phase: str | None
    start_year: int | None
    end_year: int | None
    recruiting_only: bool
    raw_query: str


def effective_filters(body: QueryRequest, intent: QueryIntent) -> EffectiveFilters:
    """Request fields override intent when present."""

    def pick(req_val: Any, int_key: str) -> Any:
        if req_val is not None and str(req_val).strip():
            return req_val
        return intent.filters.get(int_key)

    cond = pick(body.condition, "condition")
    drug = pick(body.drug_name, "drug_name")
    sponsor = pick(body.sponsor, "sponsor")
    country = pick(body.country, "country")
    phase = pick(body.trial_phase, "trial_phase")
    start_y = body.start_year if body.start_year is not None else intent.filters.get("start_year")
    end_y = body.end_year if body.end_year is not None else intent.filters.get("end_year")
    recruiting = bool(intent.filters.get("recruiting_only", False))

    comparison = intent.comparison_drug
    if isinstance(comparison, str):
        comparison = comparison.strip() or None
    else:
        comparison = None

    if isinstance(start_y, str) and start_y.isdigit():
        start_y = int(start_y)
    if isinstance(end_y, str) and end_y.isdigit():
        end_y = int(end_y)

    return EffectiveFilters(
        condition=str(cond).strip() if cond else None,
        drug_name=str(drug).strip() if drug else None,
        comparison_drug=comparison,
        sponsor=str(sponsor).strip() if sponsor else None,
        country=str(country).strip() if country else None,
        trial_phase=str(phase).strip() if phase else None,
        start_year=int(start_y) if isinstance(start_y, int) else None,
        end_year=int(end_y) if isinstance(end_y, int) else None,
        recruiting_only=recruiting,
        raw_query=body.query,
    )


def _year_range_clause(start_year: int | None, end_year: int | None) -> str | None:
    if start_year is None and end_year is None:
        return None
    lo = f"01/01/{start_year}" if start_year is not None else "MIN"
    hi = f"12/31/{end_year}" if end_year is not None else "MAX"
    return f"AREA[StartDate]RANGE[{lo}, {hi}]"


def _normalize_phase_for_api(phase: str) -> str:
    p = phase.upper().replace(" ", "").replace("-", "")
    if re.match(r"^PHASE([1234]|1/2|2/3)$", p):
        return p
    if p in {"EARLYPHASE1", "EARLY_PHASE1", "PHASE1", "PHASE2", "PHASE3", "PHASE4", "NA"}:
        return p.replace("EARLYPHASE1", "EARLY_PHASE1")
    return phase


def build_query_term(ef: EffectiveFilters, intent: QueryIntent) -> str:
    """
    Compose an advanced `query.term`.
    See: https://clinicaltrials.gov/find-studies/define-search-terms
    """
    parts: list[str] = []
    or_drug_clause: str | None = None

    if intent.viz_goal == "grouped_bar_chart" and ef.drug_name and ef.comparison_drug:
        or_drug_clause = (
            f"(AREA[InterventionName]{_q(ef.drug_name)} OR "
            f"AREA[InterventionName]{_q(ef.comparison_drug)})"
        )

    if or_drug_clause:
        parts.append(or_drug_clause)
    elif ef.drug_name:
        parts.append(_area("InterventionName", ef.drug_name))

    if ef.condition:
        parts.append(_area("ConditionSearch", ef.condition))
    if ef.sponsor:
        parts.append(_area("LeadSponsorName", ef.sponsor))
    if ef.country:
        parts.append(_area("LocationCountry", ef.country))

    yr = _year_range_clause(ef.start_year, ef.end_year)
    if yr:
        parts.append(yr)

    if ef.trial_phase:
        ph = _normalize_phase_for_api(ef.trial_phase)
        if ph:
            parts.append(f"AREA[Phase]{ph}")

    if ef.recruiting_only:
        parts.append("AREA[OverallStatus]RECRUITING")

    if not parts:
        parts.append(ef.raw_query[:500])

    term = " AND ".join(p for p in parts if p)
    return term.strip()


def meta_filter_dict(ef: EffectiveFilters) -> dict[str, Any]:
    return {
        k: v
        for k, v in {
            "condition": ef.condition,
            "drug_name": ef.drug_name,
            "comparison_drug": ef.comparison_drug,
            "sponsor": ef.sponsor,
            "country": ef.country,
            "trial_phase": ef.trial_phase,
            "start_year": ef.start_year,
            "end_year": ef.end_year,
            "recruiting_only": ef.recruiting_only,
        }.items()
        if v not in (None, "", False)
    }
