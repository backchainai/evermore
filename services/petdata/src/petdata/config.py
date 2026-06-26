"""Application configuration using pydantic-settings."""

from __future__ import annotations

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="PETDATA_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Supabase Postgres connection (postgres:// or postgresql:// URL). Empty by
    # default so the package imports without a configured database; the async
    # SQLAlchemy engine is built lazily on first request.
    database_url: SecretStr = SecretStr("")
    database_require_ssl: bool = False  # True in production (Supabase / Cloud Run)

    # Database connection pool — env-driven so each deployment target (local vs
    # Containers behind Hyperdrive) sizes its own pool without code changes.
    # Defaults preserve prior hardcoded engine behavior.
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: float = 30.0
    db_pool_recycle: int = -1
    db_pool_pre_ping: bool = True

    request_delay_ms: int = 500

    # Web server configuration
    allowed_origins: list[str] = ["http://localhost:5173"]
    debug: bool = False

    # Source Shelter Management System (SMS) extraction API. Values are empty by
    # default and supplied per-deployment via PETDATA_SMS_* env vars (see
    # .env.example); never hard-code a shelter's production endpoints here.
    cookies: str = ""
    sms_base_url: str = ""
    sms_table_animals: str = ""
    sms_table_volunteer_notes: str = ""
    sms_table_walk_records: str = ""

    # HTTP client configuration
    retry_max_attempts: int = 3
    retry_backoff_factor: float = 2.0
    retry_max_delay_ms: int = 10000
    api_timeout_seconds: float = 30.0

    @field_validator("retry_max_attempts")
    @classmethod
    def validate_max_attempts(cls, v: int) -> int:
        """Validate retry attempts is between 1 and 10."""
        if v < 1 or v > 10:
            msg = "retry_max_attempts must be between 1 and 10"
            raise ValueError(msg)
        return v

    @field_validator("request_delay_ms")
    @classmethod
    def validate_delay(cls, v: int) -> int:
        """Validate request delay is non-negative."""
        if v < 0:
            msg = "request_delay_ms must be non-negative"
            raise ValueError(msg)
        return v


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
