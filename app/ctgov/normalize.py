"""Flatten ClinicalTrials.gov v2 study JSON into `TrialRecord` for aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TrialRecord:
    nct_id: str
    brief_title: str
    overall_status: str | None
    phases: list[str]
    conditions: list[str]
    interventions: list[str]
    intervention_types: list[str]
    sponsor: str | None
    countries: list[str]
    start_year: int | None
    enrollment: int | None
    raw_excerpt_source: str
    raw: dict


@dataclass
class BucketAccum:
    count: int = 0
    trials: list[TrialRecord] = field(default_factory=list)

    def add(self, r: TrialRecord, cap: int) -> None:
        self.count += 1
        if len(self.trials) < cap:
            self.trials.append(r)


def _get_protocol(study: dict) -> dict:
    return study.get("protocolSection") or {}


def _list_str(x: object) -> list[str]:
    if not x:
        return []
    if isinstance(x, str):
        return [x.strip()] if x.strip() else []
    if isinstance(x, list):
        out: list[str] = []
        for i in x:
            if isinstance(i, str) and i.strip():
                out.append(i.strip())
        return out
    return []


def normalize_study(study: dict) -> TrialRecord:
    proto = _get_protocol(study)
    id_mod = proto.get("identificationModule") or {}
    status_mod = proto.get("statusModule") or {}
    design = proto.get("designModule") or {}
    cond_mod = proto.get("conditionsModule") or {}
    arms = proto.get("armsInterventionsModule") or {}
    loc_mod = proto.get("contactsLocationsModule") or {}

    nct = id_mod.get("nctId") or study.get("nctId") or "UNKNOWN"
    brief = id_mod.get("briefTitle") or id_mod.get("officialTitle") or ""
    org = id_mod.get("organization") or {}
    sponsor = org.get("fullName") or org.get("class")

    phases = _list_str(design.get("phases"))
    conditions = _list_str(cond_mod.get("conditions"))

    inter_names: list[str] = []
    inter_types: list[str] = []
    for inv in arms.get("interventions") or []:
        if isinstance(inv, dict):
            n = inv.get("name")
            if isinstance(n, str) and n.strip():
                inter_names.append(n.strip())
            t = inv.get("type")
            if isinstance(t, str) and t.strip():
                inter_types.append(t.strip())

    countries: list[str] = []
    for loc in loc_mod.get("locations") or []:
        if isinstance(loc, dict):
            c = loc.get("country")
            if isinstance(c, str) and c.strip():
                countries.append(c.strip())

    start_year: int | None = None
    sds = status_mod.get("startDateStruct") or {}
    date_s = sds.get("date")
    if isinstance(date_s, str) and len(date_s) >= 4 and date_s[:4].isdigit():
        start_year = int(date_s[:4])

    enrollment: int | None = None
    en = design.get("enrollmentInfo") or {}
    if isinstance(en.get("count"), int):
        enrollment = en["count"]

    overall = status_mod.get("overallStatus")
    if not isinstance(overall, str):
        overall = None

    excerpt_bits = [brief[:280]] + conditions[:2] + inter_names[:2]
    excerpt = " | ".join(b for b in excerpt_bits if b)

    return TrialRecord(
        nct_id=nct,
        brief_title=brief if isinstance(brief, str) else "",
        overall_status=overall,
        phases=phases or ["UNKNOWN"],
        conditions=conditions,
        interventions=inter_names,
        intervention_types=inter_types,
        sponsor=sponsor if isinstance(sponsor, str) else None,
        countries=sorted(set(countries)) if countries else ["Unknown"],
        start_year=start_year,
        enrollment=enrollment,
        raw_excerpt_source=excerpt[:500],
        raw=study,
    )
