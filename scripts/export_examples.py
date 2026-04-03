"""Write example response JSON files under examples/ (offline, no CT.gov call)."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import Settings
from app.ctgov.normalize import normalize_study
from app.ctgov.query_builder import EffectiveFilters
from app.intent.models import QueryIntent
from app.viz.engine import build_visualization

FIXTURE = ROOT / "tests" / "fixtures" / "min_study.json"
OUT = ROOT / "examples"


def base_study() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def variant_study(
    *,
    nct: str,
    year: int,
    phase: str,
    drug: str,
    sponsor: str,
    country: str = "United States",
    recruiting: bool = True,
) -> dict:
    d = deepcopy(base_study())
    d["protocolSection"]["identificationModule"]["nctId"] = nct
    d["protocolSection"]["identificationModule"]["organization"]["fullName"] = sponsor
    d["protocolSection"]["statusModule"]["startDateStruct"]["date"] = f"{year}-03-15"
    d["protocolSection"]["statusModule"]["overallStatus"] = (
        "RECRUITING" if recruiting else "COMPLETED"
    )
    d["protocolSection"]["designModule"]["phases"] = [phase]
    d["protocolSection"]["armsInterventionsModule"]["interventions"] = [
        {"type": "DRUG", "name": drug},
    ]
    d["protocolSection"]["contactsLocationsModule"] = {
        "locations": [{"country": country, "city": "Demo City"}],
        "centralContacts": [],
    }
    return d


def dump(name: str, resp) -> None:
    OUT.mkdir(exist_ok=True)
    p = OUT / name
    p.write_text(json.dumps(resp.model_dump(mode="json"), indent=2), encoding="utf-8")
    print("wrote", p.relative_to(ROOT))


def main() -> None:
    settings = Settings()

    s1 = base_study()
    records = [normalize_study(s1)]
    ef = EffectiveFilters(
        condition="diabetes",
        drug_name=None,
        comparison_drug=None,
        sponsor=None,
        country=None,
        trial_phase=None,
        start_year=None,
        end_year=None,
        recruiting_only=False,
        raw_query="offline demo",
    )
    dump(
        "example_01_bar_chart_phase.json",
        build_visualization(
            QueryIntent(viz_goal="bar_chart", dimension_hint="phase"),
            ef,
            records,
            [],
            settings,
            "AREA[ConditionSearch]diabetes",
        ),
    )

    studies = [
        variant_study(
            nct="NCT10000001",
            year=2019,
            phase="PHASE1",
            drug="DrugA",
            sponsor="Sponsor One",
        ),
        variant_study(
            nct="NCT10000002",
            year=2020,
            phase="PHASE2",
            drug="DrugB",
            sponsor="Sponsor Two",
        ),
        variant_study(
            nct="NCT10000003",
            year=2021,
            phase="PHASE2",
            drug="DrugA",
            sponsor="Sponsor One",
        ),
    ]
    rec2 = [normalize_study(x) for x in studies]
    dump(
        "example_02_time_series.json",
        build_visualization(
            QueryIntent(viz_goal="time_series", dimension_hint="year"),
            ef,
            rec2,
            [],
            settings,
            "diabetes",
        ),
    )

    dump(
        "example_03_histogram_start_year.json",
        build_visualization(
            QueryIntent(viz_goal="histogram", dimension_hint="start_year"),
            ef,
            rec2,
            [],
            settings,
            "diabetes",
        ),
    )

    dump(
        "example_04_network_sponsor_drug.json",
        build_visualization(
            QueryIntent(viz_goal="network_graph"),
            ef,
            rec2,
            [],
            settings,
            "diabetes",
        ),
    )

    ef_ab = EffectiveFilters(
        condition="diabetes",
        drug_name="DrugA",
        comparison_drug="DrugB",
        sponsor=None,
        country=None,
        trial_phase=None,
        start_year=None,
        end_year=None,
        recruiting_only=False,
        raw_query="compare DrugA vs DrugB",
    )
    dump(
        "example_05_grouped_bar_two_drugs.json",
        build_visualization(
            QueryIntent(
                viz_goal="grouped_bar_chart",
                dimension_hint="phase",
                comparison_drug="DrugB",
            ),
            ef_ab,
            rec2,
            [],
            settings,
            "AREA[InterventionName]DrugA OR AREA[InterventionName]DrugB",
        ),
    )

    dump(
        "example_06_scatter_enrollment_vs_year.json",
        build_visualization(
            QueryIntent(viz_goal="scatter_plot"),
            ef,
            rec2,
            [],
            settings,
            "diabetes",
        ),
    )

    geo_studies = [
        variant_study(
            nct="NCT20000001",
            year=2022,
            phase="PHASE2",
            drug="GeoDrug",
            sponsor="Global Sponsor A",
            country="United States",
            recruiting=True,
        ),
        variant_study(
            nct="NCT20000002",
            year=2023,
            phase="PHASE3",
            drug="GeoDrug",
            sponsor="Global Sponsor B",
            country="Canada",
            recruiting=True,
        ),
    ]
    rec_geo = [normalize_study(x) for x in geo_studies]
    ef_geo = EffectiveFilters(
        condition="diabetes",
        drug_name=None,
        comparison_drug=None,
        sponsor=None,
        country=None,
        trial_phase=None,
        start_year=None,
        end_year=None,
        recruiting_only=True,
        raw_query="Which countries have the most recruiting diabetes trials?",
    )
    dump(
        "example_07_geographic_country_recruiting.json",
        build_visualization(
            QueryIntent(
                viz_goal="bar_chart",
                dimension_hint="country",
                notes="Appendix: geographic / recruiting pattern.",
            ),
            ef_geo,
            rec_geo,
            [],
            settings,
            "AREA[ConditionSearch]diabetes AND AREA[OverallStatus]RECRUITING",
        ),
    )


if __name__ == "__main__":
    main()
