"""Application configuration using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="GRADER_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Web server configuration
    allowed_origins: list[str] = ["http://localhost:5173"]
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
