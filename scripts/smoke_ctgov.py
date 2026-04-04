"""Check ClinicalTrials.gov from Python using the same client as the API (run from repo root)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow `python scripts/smoke_ctgov.py` without PYTHONPATH=.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.config import Settings
from app.ctgov.client import fetch_studies


async def main() -> int:
    settings = Settings()
    print("HTTP backend:", settings.ctgov_http_backend)
    print("URL:", settings.ctgov_base_url)
    print("User-Agent (first 72 chars):", settings.ctgov_user_agent[:72])
    studies, warnings = await fetch_studies("heart", settings)
    for w in warnings:
        print("warning:", w)
    print("studies count:", len(studies))
    if studies:
        nct = (
            studies[0]
            .get("protocolSection", {})
            .get("identificationModule", {})
            .get("nctId")
        )
        print("first nctId:", nct)
    if warnings and any("403" in w for w in warnings):
        print(
            "\nIf the browser works but this fails: restart uvicorn after code changes,",
            "set CTGOV_USER_AGENT in .env to match your browser, or set HTTPS_PROXY",
            "if your browser uses a corporate proxy (Python does not auto-use Windows PAC).",
            sep="\n",
        )
        return 1
    if not studies:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
