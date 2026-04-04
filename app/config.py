"""Application settings from environment."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str | None = None

    ctgov_base_url: str = "https://clinicaltrials.gov/api/v2/studies"
    ctgov_max_studies: int = 1000
    ctgov_page_size: int = 100
    ctgov_timeout_seconds: float = 60.0
    # Many deployments use a CDN/WAF that returns 403 for obviously scripted clients.
    # Override with CTGOV_USER_AGENT if your network still blocks requests.
    ctgov_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    ctgov_referer: str = "https://clinicaltrials.gov/"
    # curl_cffi mimics Chrome TLS (JA3/HTTP2); many CDNs block plain httpx/Python ssl.
    # Set CTGOV_HTTP_BACKEND=httpx to force the legacy client (may 403 on some networks).
    ctgov_http_backend: Literal["curl_cffi", "httpx"] = "curl_cffi"
    ctgov_curl_impersonate: str = "chrome"

    citation_excerpts_per_datum: int = 3
    citation_trials_per_bucket_cap: int = 50
