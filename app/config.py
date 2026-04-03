"""Application settings from environment."""

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

    citation_excerpts_per_datum: int = 3
    citation_trials_per_bucket_cap: int = 50
