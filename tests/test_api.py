"""HTTP contract and pipeline smoke tests (no live ClinicalTrials.gov calls)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_query_missing_body_validation(client: TestClient) -> None:
    r = client.post("/v1/query", json={})
    assert r.status_code == 422


def test_query_blank_query_validation(client: TestClient) -> None:
    r = client.post("/v1/query", json={"query": "   "})
    assert r.status_code == 422


def test_query_year_order_validation(client: TestClient) -> None:
    r = client.post(
        "/v1/query",
        json={"query": "Trials", "start_year": 2020, "end_year": 2010},
    )
    assert r.status_code == 422


def test_query_api_failure_returns_no_hallucinated_counts(monkeypatch, client: TestClient) -> None:
    async def _fail_fetch(*args, **kwargs):  # noqa: ARG001
        return [], ["ClinicalTrials.gov returned HTTP 503: upstream"]

    import app.main as main_mod

    monkeypatch.setattr(main_mod, "fetch_studies", _fail_fetch)

    r = client.post("/v1/query", json={"query": "Breast cancer trials by phase"})
    assert r.status_code == 200
    payload = r.json()
    assert payload["visualization"]["type"] == "bar_chart"
    assert payload["visualization"]["data"][0].get("trial_count") == 0
    assert payload["meta"]["source"]["result_count"] == 0
    assert payload["meta"]["warnings"]
