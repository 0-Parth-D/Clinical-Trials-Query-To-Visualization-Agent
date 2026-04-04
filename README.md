# ClinicalTrials.gov Query-to-Visualization Agent

Backend service that accepts natural-language questions (plus optional structured filters), retrieves studies from the [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api), and returns a **single frontend-ready visualization specification** with **metadata** and optional **deep citations** (`nct_id` + verbatim excerpt from normalized trial text).

## Quick start

```powershell
cd "path\to\Clinical-Trials-Query-To-Visualization-Agent"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # optional: add OPENAI_API_KEY
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Web UI (optional)

From repo root:

```powershell
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000` by default, so you usually **do not** need `VITE_API_BASE_URL`. See [frontend/.env.example](frontend/.env.example).

### Health check

`GET /health` → `{"status":"ok"}`

### Main endpoint

`POST /v1/query` with JSON body (see OpenAPI for full schema and examples).

## Request schema (`POST /v1/query`)

| Field | Type | Required | Description |
|--------|------|----------|-------------|
| `query` | string | yes | Natural-language clinical trials question (non-empty after trim). |
| `drug_name` | string | no | Primary intervention/drug; merged into CT.gov `query.term`. |
| `comparison_drug` | string | no | Second intervention for **grouped bar** (A vs B). Prefer this field; see also `extra_filters`. |
| `condition` | string | no | Condition/disease hint. |
| `trial_phase` | string | no | Phase hint (passed into `query.term` when present). |
| `sponsor` | string | no | Lead sponsor name hint. |
| `country` | string | no | Location country hint. |
| `start_year` / `end_year` | int | no | Inclusive start-year window via `AREA[StartDate]RANGE[...]`. Must satisfy `start_year <= end_year`. |
| `extra_filters` | object | no | Forward-compatible bag; legacy `comparison_drug` here still works if top-level `comparison_drug` is omitted. |

Structured fields **override** the same keys from LLM/heuristic intent when supplied. Top-level `drug_name` / `comparison_drug` take precedence over duplicate keys inside `extra_filters` for the comparison pair.

## Response schema

Top level:

- `visualization`: `type`, `title`, `encoding`, `data`
- `meta`: `units`, `sort`, `time_granularity`, `group_by`, `filters`, `source`, `assumptions`, `warnings`

`visualization.type` is one of:

- `bar_chart` — rows: `phase` or `country`, `trial_count`, `citations[]`
- `grouped_bar_chart` — `phase`, `series` (drug label), `trial_count`, `citations[]`
- `time_series` / `histogram` — year/`bin_start`, `trial_count`, `citations[]`
- `scatter_plot` — `start_year`, `enrollment`, `nct_id`, `citations[]`
- `network_graph` — `data[0].nodes` and `data[0].edges` (`source`, `target`, `weight`, `citations[]`)

Each `citations` entry: `{ "nct_id": "...", "excerpt": "..." }` (excerpt from brief title / conditions / interventions in the API payload).

## AI / intent

- If `OPENAI_API_KEY` is set, the service asks the model for a **JSON intent only** (filters + `viz_goal` + `comparison_drug` when relevant). **Counts are never taken from the model**; aggregation is deterministic over API results.
- LLM output is **post-processed**: e.g. if the request includes **`drug_name` + `comparison_drug`**, intent is promoted to **`grouped_bar_chart`** when the query is not explicitly asking for a **per-country** breakdown; phrases like “by country” override to a **country bar** and ignore a stale comparison field.
- If the key is missing or the call fails, a **heuristic** classifier uses keywords in `query` (e.g. “network”, “trend”, “vs”/“versus”, “histogram”, “by country”) plus structured fields.

Environment variables (see [.env.example](.env.example)):

- `OPENAI_API_KEY`, optional `OPENAI_BASE_URL`, `OPENAI_MODEL`
- `CTGOV_MAX_STUDIES`, `CTGOV_PAGE_SIZE`, `CTGOV_BASE_URL`, `CTGOV_TIMEOUT_SECONDS`
- `CTGOV_HTTP_BACKEND` — default **`curl_cffi`** (browser-like TLS); set to **`httpx`** to force the legacy client if needed
- `CTGOV_CURL_IMPERSONATE` — e.g. `chrome` (used with curl_cffi)
- Optional `CTGOV_USER_AGENT`, `CTGOV_REFERER`; proxy via `HTTPS_PROXY` / `HTTP_PROXY` if required
- `CITATION_EXCERPTS_PER_DATUM`, `CITATION_TRIALS_PER_BUCKET_CAP`

## Design choices and tradeoffs

- **Single pipeline** — one code path: intent → `query.term` → fetch → normalize → viz engine. Avoids per-query one-offs.
- **Grounding** — bar/time/network values always come from normalized trial records; empty API results yield an explicit zero row, not fabricated numbers.
- **Pagination cap** — default max studies is configurable to keep latency bounded; `meta.warnings` may note truncation.
- **Multi-value trials** — a trial with multiple phases contributes to each phase bucket; multi-country sites contribute to each country bucket (documented in `meta.assumptions`).
- **Grouped drug comparison** — requires **`drug_name` and `comparison_drug`** (top-level preferred; `extra_filters.comparison_drug` is still supported). When both are present in **effective filters**, the CT.gov `query.term` uses **`(InterventionName A OR InterventionName B)`** so the result set includes either drug.
- **403 / blocking** — many networks reject non-browser TLS fingerprints. This repo defaults to **`curl_cffi`** with Chrome impersonation; if issues persist, try another network/VPN, proxy env vars, or tune `CTGOV_USER_AGENT` / `CTGOV_REFERER` (see `.env.example`).

## Example runs (offline fixtures)

The folder [examples/](examples/) contains **seven JSON responses** produced by this codebase using normalized fixture trials (no live API). They double as the assignment’s “example runs” and are validated in CI via `tests/test_examples_validate.py`. Regenerate:

```powershell
.\.venv\Scripts\python.exe scripts\export_examples.py
```

| Appendix category (assignment) | Example file |
|--------------------------------|--------------|
| Time trends | [examples/example_02_time_series.json](examples/example_02_time_series.json) |
| Distributions | [examples/example_01_bar_chart_phase.json](examples/example_01_bar_chart_phase.json), [examples/example_03_histogram_start_year.json](examples/example_03_histogram_start_year.json) |
| Comparisons | [examples/example_05_grouped_bar_two_drugs.json](examples/example_05_grouped_bar_two_drugs.json) |
| Geographic / recruiting | [examples/example_07_geographic_country_recruiting.json](examples/example_07_geographic_country_recruiting.json) |
| Networks | [examples/example_04_network_sponsor_drug.json](examples/example_04_network_sponsor_drug.json) |
| Scatter | [examples/example_06_scatter_enrollment_vs_year.json](examples/example_06_scatter_enrollment_vs_year.json) |

For **live** responses, run the server and POST to `/v1/query` (see OpenAPI examples).

## Tests

Run from the **repository root** after `pip install -r requirements.txt` (`pytest.ini` sets `pythonpath = .`; `tests/conftest.py` also prepends the root for older pytest):

```powershell
cd "path\to\Clinical-Trials-Query-To-Visualization-Agent"
python -m pytest -q
```

These cover HTTP validation (`422` on bad requests), the “API failure” path (no fabricated counts), deterministic aggregation, citation excerpts, example JSON contract parsing, and LLM-invalid `viz_goal` coercion.

## Submission zip and verification gate

Follow [docs/SUBMISSION_AND_VERIFICATION.md](docs/SUBMISSION_AND_VERIFICATION.md) for the full checklist. Quick packaging options:

```powershell
git archive -o clinical-trials-viz-agent.zip HEAD
```

or

```powershell
powershell -ExecutionPolicy Bypass -File scripts/make_submission_zip.ps1
```

Do not include `.env` or `.venv` in the archive; use [.env.example](.env.example) only.

## Project layout

- [app/main.py](app/main.py) — FastAPI app
- [app/config.py](app/config.py) — settings
- [app/ctgov/](app/ctgov/) — API client, `query.term` builder, normalization
- [app/intent/](app/intent/) — LLM + heuristic intent + request merges (grouped / country)
- [app/viz/engine.py](app/viz/engine.py) — aggregations + citation attachment
- [frontend/](frontend/) — Vite + React UI (`POST /v1/query` via `/api` proxy in dev)
- [tests/](tests/) — unit tests with [tests/fixtures/min_study.json](tests/fixtures/min_study.json)

## Limitations and next steps

- Richer geography (US states, site lat/long maps) and outcome-level analytics would need more fields and caching.
- Phase/status filters depend on CT.gov advanced query behavior; edge cases may require manual `query.term` tuning.
- Stronger LLM validation (tool calls, self-check against returned N) could further reduce misclassified `viz_goal`.
