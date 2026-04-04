"""Turn normalized trials + intent into VisualizationResponse."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from app.config import Settings
from app.ctgov.normalize import BucketAccum, TrialRecord
from app.ctgov.query_builder import EffectiveFilters, meta_filter_dict
from app.intent.models import QueryIntent
from app.schemas import MetaBlock, SourceMeta, VisualizationResponse, VisualizationSpec, VizType


def _human_phase(p: str) -> str:
    if p in ("UNKNOWN", "NA"):
        return "Unknown"
    x = p.upper().replace("_", " ").replace("PHASE/", " / ")
    if "PHASE" in x and "EARLY" not in x:
        return x.replace("PHASE", "Phase ").replace("  ", " ").strip()
    return x.title()


def _intervention_matches(record: TrialRecord, name: str | None) -> bool:
    if not name:
        return False
    n = name.strip().lower()
    if not n:
        return False
    for inter in record.interventions:
        il = inter.lower()
        if n in il:
            return True
    # Substring match on significant tokens (helps generic vs trade names on CT.gov).
    for token in re.findall(r"[a-z0-9][a-z0-9\-]{3,}", n):
        for inter in record.interventions:
            if token in inter.lower():
                return True
    return False


def _citations(
    trials: list[TrialRecord],
    settings: Settings,
) -> list[dict[str, str]]:
    k = max(0, settings.citation_excerpts_per_datum)
    out: list[dict[str, str]] = []
    for t in trials[:k]:
        out.append({"nct_id": t.nct_id, "excerpt": (t.raw_excerpt_source or t.brief_title)[:450]})
    return out


def _coerce_viz(goal: str) -> VizType:
    try:
        return VizType(goal)
    except ValueError:
        return VizType.bar_chart


def build_visualization(
    intent: QueryIntent,
    ef: EffectiveFilters,
    records: list[TrialRecord],
    warnings: list[str],
    settings: Settings,
    query_term: str,
) -> VisualizationResponse:
    retrieved_at = datetime.now(timezone.utc)
    viz_t = _coerce_viz(intent.viz_goal)
    if viz_t == VizType.grouped_bar_chart and not (ef.drug_name and ef.comparison_drug):
        return build_visualization(
            intent.model_copy(update={"viz_goal": "bar_chart"}),
            ef,
            records,
            warnings
            + [
                "Grouped bar chart needs drug_name and comparison_drug; "
                "falling back to phase distribution."
            ],
            settings,
            query_term,
        )
    dim = intent.dimension_hint or "phase"
    meta_filters = meta_filter_dict(ef)
    meta_filters["query_term"] = query_term

    assumptions = [
        "Counts are derived only from studies returned by ClinicalTrials.gov for the built query.term.",
        "Multi-phase trials are counted once per phase label present in the study record.",
    ]
    if intent.notes:
        assumptions.append(intent.notes)

    warn_merge = list(warnings) if warnings else []
    cap = settings.citation_trials_per_bucket_cap

    if not records:
        spec = VisualizationSpec(
            type=viz_t,
            title="No studies returned",
            encoding={"x": "message", "y": "trial_count"},
            data=[{"message": "No matching trials", "trial_count": 0, "citations": []}],
        )
        return VisualizationResponse(
            visualization=spec,
            meta=MetaBlock(
                units="trials",
                sort=None,
                time_granularity=None,
                group_by=None,
                filters=meta_filters,
                source=SourceMeta(
                    name="ClinicalTrials.gov",
                    api=settings.ctgov_base_url,
                    retrieved_at=retrieved_at,
                    result_count=0,
                ),
                assumptions=assumptions,
                warnings=warn_merge or None,
            ),
        )

    # --- viz branches ---
    if viz_t == VizType.grouped_bar_chart and ef.drug_name and ef.comparison_drug:
        buckets: dict[tuple[str, str], BucketAccum] = defaultdict(BucketAccum)
        for r in records:
            matched_series: list[str] = []
            if _intervention_matches(r, ef.drug_name):
                matched_series.append(ef.drug_name)
            if _intervention_matches(r, ef.comparison_drug):
                matched_series.append(ef.comparison_drug)
            for ph in r.phases:
                ph_h = _human_phase(ph)
                for series in matched_series:
                    buckets[(ph_h, series)].add(r, cap)
        rows: list[dict[str, Any]] = []
        for (phase, series), acc in sorted(buckets.items(), key=lambda x: (x[0][0], x[0][1])):
            rows.append(
                {
                    "phase": phase,
                    "series": series,
                    "trial_count": acc.count,
                    "citations": _citations(acc.trials, settings),
                }
            )
        title = f"Trials by phase: {ef.drug_name} vs {ef.comparison_drug}"
        spec = VisualizationSpec(
            type=VizType.grouped_bar_chart,
            title=title,
            encoding={
                "x": "phase",
                "y": "trial_count",
                "series": "series",
                "color": "series",
            },
            data=rows,
        )
        group_by = "phase,series"

    elif viz_t == VizType.time_series or (viz_t == VizType.bar_chart and dim == "year"):
        buckets = defaultdict(BucketAccum)
        for r in records:
            y = r.start_year
            if y is None:
                buckets["Unknown"].add(r, cap)
            else:
                buckets[str(y)].add(r, cap)
        rows = []
        def _year_key(item: tuple[str, BucketAccum]) -> tuple[bool, int]:
            lab = item[0]
            if lab == "Unknown":
                return True, 0
            return False, int(lab) if lab.isdigit() else 0

        for label, acc in sorted(buckets.items(), key=_year_key):
            rows.append(
                {
                    "year": int(label) if label != "Unknown" and label.isdigit() else label,
                    "trial_count": acc.count,
                    "citations": _citations(acc.trials, settings),
                }
            )
        spec = VisualizationSpec(
            type=VizType.time_series,
            title="Trials by start year",
            encoding={"x": "year", "y": "trial_count"},
            data=rows,
        )
        group_by = "year"
        viz_t = VizType.time_series

    elif viz_t == VizType.histogram:
        buckets = defaultdict(BucketAccum)
        for r in records:
            y = r.start_year
            key = str(y) if y is not None else "Unknown"
            buckets[key].add(r, cap)
        rows = []
        for label, acc in sorted(
            buckets.items(),
            key=lambda x: (x[0] == "Unknown", int(x[0]) if x[0].isdigit() else 0),
        ):
            rows.append(
                {
                    "bin_start": int(label) if label != "Unknown" and label.isdigit() else label,
                    "trial_count": acc.count,
                    "citations": _citations(acc.trials, settings),
                }
            )
        spec = VisualizationSpec(
            type=VizType.histogram,
            title="Distribution of trials by start year",
            encoding={"x": "bin_start", "y": "trial_count"},
            data=rows,
        )
        group_by = "start_year"

    elif viz_t == VizType.scatter_plot:
        rows = []
        for r in records:
            if r.start_year is None or r.enrollment is None:
                continue
            rows.append(
                {
                    "start_year": r.start_year,
                    "enrollment": r.enrollment,
                    "nct_id": r.nct_id,
                    "citations": _citations([r], settings),
                }
            )
        if not rows:
            warn_merge.append("No trials with both start year and reported enrollment; showing phase bars instead.")
            return build_visualization(
                QueryIntent(
                    filters=intent.filters,
                    viz_goal="bar_chart",
                    dimension_hint="phase",
                    comparison_drug=intent.comparison_drug,
                    notes=intent.notes,
                ),
                ef,
                records,
                warn_merge,
                settings,
                query_term,
            )
        spec = VisualizationSpec(
            type=VizType.scatter_plot,
            title="Enrollment vs start year",
            encoding={"x": "start_year", "y": "enrollment", "id": "nct_id"},
            data=rows,
        )
        group_by = None

    elif viz_t == VizType.network_graph:
        nodes: dict[str, dict[str, str]] = {}
        edge_trials: dict[tuple[str, str], list[TrialRecord]] = defaultdict(list)

        def node_id(kind: str, label: str) -> str:
            safe = label.strip() or "Unknown"
            return f"{kind}:{safe[:80]}"

        for r in records:
            sp = (r.sponsor or "Unknown sponsor").strip()
            sid = node_id("sponsor", sp)
            if sid not in nodes:
                nodes[sid] = {"id": sid, "label": sp[:120], "kind": "sponsor"}
            drug_names: list[str] = []
            for idx, inter in enumerate(r.interventions):
                typ = (
                    r.intervention_types[idx]
                    if idx < len(r.intervention_types)
                    else ""
                )
                if not typ or "DRUG" in typ.upper() or "BIOLOGIC" in typ.upper():
                    drug_names.append(inter)
            if not drug_names:
                drug_names = r.interventions[:3]
            for d in drug_names[:5]:
                label = (d or "").strip() or "Unknown drug"
                did = node_id("drug", label)
                if did not in nodes:
                    nodes[did] = {"id": did, "label": label[:120], "kind": "drug"}
                edge_trials[(sid, did)].append(r)

        edge_list: list[dict[str, Any]] = []
        for (sid, did), trs in edge_trials.items():
            acc = BucketAccum()
            for t in trs[:cap]:
                acc.add(t, cap)
            edge_list.append(
                {
                    "source": sid,
                    "target": did,
                    "weight": len(trs),
                    "citations": _citations(trs, settings),
                }
            )
        edge_list.sort(key=lambda e: -e["weight"])
        spec = VisualizationSpec(
            type=VizType.network_graph,
            title="Sponsor ↔ drug network (trial co-occurrence)",
            encoding={
                "nodes": "nodes",
                "edges": "edges",
                "source": "source",
                "target": "target",
                "weight": "weight",
            },
            data=[
                {
                    "nodes": list(nodes.values()),
                    "edges": edge_list[:500],
                }
            ],
        )
        group_by = "sponsor,drug"

    elif dim == "country":
        buckets = defaultdict(BucketAccum)
        for r in records:
            for c in r.countries:
                buckets[c].add(r, cap)
        rows = []
        for country, acc in sorted(buckets.items(), key=lambda x: -x[1].count):
            rows.append(
                {
                    "country": country,
                    "trial_count": acc.count,
                    "citations": _citations(acc.trials, settings),
                }
            )
        if len(rows) == 1 and rows[0].get("country") == "Unknown":
            warn_merge.append(
                "No facility countries were found on the returned studies; "
                "everything is grouped as 'Unknown'. Location fields are sometimes "
                "missing from API list payloads for individual hits."
            )
        spec = VisualizationSpec(
            type=VizType.bar_chart,
            title="Trials by country (site locations)",
            encoding={"x": "country", "y": "trial_count"},
            data=rows,
        )
        group_by = "country"

    else:
        # Default: phase distribution
        buckets = defaultdict(BucketAccum)
        for r in records:
            for ph in r.phases:
                buckets[_human_phase(ph)].add(r, cap)
        rows = []
        for phase, acc in sorted(buckets.items(), key=lambda x: x[0]):
            rows.append(
                {
                    "phase": phase,
                    "trial_count": acc.count,
                    "citations": _citations(acc.trials, settings),
                }
            )
        spec = VisualizationSpec(
            type=VizType.bar_chart,
            title="Trials by phase",
            encoding={"x": "phase", "y": "trial_count"},
            data=rows,
        )
        group_by = "phase"

    return VisualizationResponse(
        visualization=spec,
        meta=MetaBlock(
            units="trials",
            sort=None,
            time_granularity="year" if spec.type in (VizType.time_series, VizType.histogram) else None,
            group_by=group_by,
            filters=meta_filters,
            source=SourceMeta(
                name="ClinicalTrials.gov",
                api=settings.ctgov_base_url,
                retrieved_at=retrieved_at,
                result_count=len(records),
            ),
            assumptions=assumptions,
            warnings=warn_merge or None,
        ),
    )
