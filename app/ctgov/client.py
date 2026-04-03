"""Paginated fetch from ClinicalTrials.gov API v2."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "ClinicalTrialsVizAgent/1.0 (educational; https://clinicaltrials.gov/data-api)"
    ),
    "Accept": "application/json",
}


async def fetch_studies(query_term: str, settings: Settings) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Returns (studies, warnings). Stops after ctgov_max_studies.
    """
    warnings: list[str] = []
    out: list[dict[str, Any]] = []
    token: str | None = None

    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=settings.ctgov_timeout_seconds) as client:
        while len(out) < settings.ctgov_max_studies:
            page_size = min(
                settings.ctgov_page_size,
                settings.ctgov_max_studies - len(out),
            )
            params: dict[str, str | int] = {
                "query.term": query_term,
                "pageSize": page_size,
            }
            if token:
                params["pageToken"] = token

            r = await client.get(settings.ctgov_base_url, params=params)
            if r.status_code != 200:
                msg = f"ClinicalTrials.gov returned HTTP {r.status_code}"
                try:
                    msg += f": {r.text[:300]}"
                except Exception:
                    pass
                logger.warning(msg)
                warnings.append(msg)
                break

            payload = r.json()
            batch = payload.get("studies") or []
            out.extend(batch)

            token = payload.get("nextPageToken")
            if not token or not batch:
                break

        if len(out) > settings.ctgov_max_studies:
            out = out[: settings.ctgov_max_studies]
            warnings.append(
                f"Truncated at {settings.ctgov_max_studies} studies "
                "(set CTGOV_MAX_STUDIES to raise the cap)."
            )

    return out, warnings
