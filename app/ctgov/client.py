"""Paginated fetch from ClinicalTrials.gov API v2."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


def _request_headers(settings: Settings) -> dict[str, str]:
    return {
        "User-Agent": settings.ctgov_user_agent,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": settings.ctgov_referer,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }


def _proxies_from_environ() -> dict[str, str] | None:
    https = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    http = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    if not https and not http:
        return None
    out: dict[str, str] = {}
    if http:
        out["http"] = http
    if https:
        out["https"] = https
    return out or None


async def _fetch_studies_httpx(
    query_term: str,
    settings: Settings,
    headers: dict[str, str],
) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    out: list[dict[str, Any]] = []
    token: str | None = None

    async with httpx.AsyncClient(
        headers=headers,
        timeout=settings.ctgov_timeout_seconds,
        follow_redirects=True,
    ) as client:
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


async def _fetch_studies_curl_cffi(
    query_term: str,
    settings: Settings,
    headers: dict[str, str],
) -> tuple[list[dict[str, Any]], list[str]]:
    # Imported only when this backend is selected (tests may not need curl_cffi).
    from curl_cffi import AsyncSession

    warnings: list[str] = []
    out: list[dict[str, Any]] = []
    token: str | None = None
    proxies = _proxies_from_environ()

    async with AsyncSession() as session:
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

            req_kw: dict[str, Any] = {
                "params": params,
                "headers": headers,
                "impersonate": settings.ctgov_curl_impersonate,
                "timeout": settings.ctgov_timeout_seconds,
            }
            if proxies:
                req_kw["proxies"] = proxies

            r = await session.get(settings.ctgov_base_url, **req_kw)
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


async def fetch_studies(query_term: str, settings: Settings) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Returns (studies, warnings). Stops after ctgov_max_studies.

    Prefers curl_cffi + browser TLS impersonation by default because many networks
    return HTTP 403 for Python/httpx TLS fingerprints to ClinicalTrials.gov.
    """
    headers = _request_headers(settings)
    if settings.ctgov_http_backend == "curl_cffi":
        try:
            import curl_cffi  # noqa: F401
        except ImportError:
            logger.warning(
                "curl_cffi is not installed (pip install curl_cffi); "
                "falling back to httpx; requests may return HTTP 403."
            )
        else:
            return await _fetch_studies_curl_cffi(query_term, settings, headers)
    return await _fetch_studies_httpx(query_term, settings, headers)
