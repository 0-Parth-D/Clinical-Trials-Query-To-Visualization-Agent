import json
from pathlib import Path

from app.ctgov.normalize import normalize_study


def test_normalize_min_study() -> None:
    raw = json.loads((Path(__file__).parent / "fixtures" / "min_study.json").read_text(encoding="utf-8"))
    r = normalize_study(raw)
    assert r.nct_id == "NCT09999999"
    assert r.start_year == 2020
    assert r.enrollment == 120
    assert r.phases[0] == "PHASE2"
    assert "Metformin" in " ".join(r.interventions)
    assert r.sponsor == "Example Pharma Inc."
    assert "United States" in r.countries
    assert "NCT09999999" in r.raw_excerpt_source or "Example" in r.raw_excerpt_source
