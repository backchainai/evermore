# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Application configuration via pydantic-settings."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env at the service root (services/retriever/.env)
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

# Default CORS origins for local development
_DEFAULT_ORIGINS = "http://localhost:5173,http://localhost:3000"


def _parse_origins_str(raw: str) -> list[str]:
    """Parse an origins string into a list.

    Accepts JSON arrays or comma-separated values:
      '["http://a","http://b"]'  → ["http://a", "http://b"]
      'http://a,http://b'       → ["http://a", "http://b"]
      '[\"http://a\"]'          → ["http://a"]  (shell-escaped)
    """
    raw = raw.strip()
    if not raw:
        return []
    if raw.startswith("["):
        try:
            result = json.loads(raw)
            if isinstance(result, list):
                return [str(s) for s in result]
        except json.JSONDecodeError:
            # Shell-mangled JSON — strip brackets, split, clean quotes
            return [s.strip().strip("\"'") for s in raw[1:-1].split(",") if s.strip()]
    return [s.strip() for s in raw.split(",") if s.strip()]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: SecretStr = SecretStr("")
    supabase_service_role_key: SecretStr = SecretStr("")
    database_url: SecretStr = SecretStr("")

    # OpenRouter
    openrouter_api_key: SecretStr = SecretStr("")

    # OpenAI
    openai_api_key: SecretStr = SecretStr("")

    # Langfuse
    langfuse_secret_key: SecretStr = SecretStr("")
    langfuse_public_key: str = ""
    langfuse_host: str = "https://us.cloud.langfuse.com"

    # Cloudflare AI Gateway
    cloudflare_account_id: str = ""
    cloudflare_gateway_id: str = ""

    # GCP
    gcp_project_id: str = ""

    # OpenTelemetry
    otel_enabled: bool = True
    otel_trace_sample_rate: float = 1.0
    otel_exporter_otlp_endpoint: str = ""

    # Database
    database_require_ssl: bool = False  # True in production (Supabase / Cloud Run)

    # LLM
    default_llm_model: str = "anthropic/claude-sonnet-4"
    default_embedding_model: str = "openai/text-embedding-3-small"
    llm_timeout_seconds: float = 30.0

    # Safety
    moderation_enabled: bool = True

    # RAG
    rag_top_k: int = 5

    # Docling document processing
    docling_ocr_enabled: bool = True
    docling_table_extraction: bool = True
    docling_picture_description: bool = False
    docling_max_pages: int = 100
    docling_chunk_max_tokens: int = 512
    docling_merge_peers: bool = True

    # Hybrid retrieval
    hybrid_retrieval_enabled: bool = True
    hybrid_semantic_weight: float = 0.5
    hybrid_keyword_weight: float = 0.5
    hybrid_rrf_k: int = 60

    # Cache
    cache_enabled: bool = True
    cache_similarity_threshold: float = 0.95

    # Conversation
    conversation_max_messages: int = 20

    # App
    debug: bool = False
    # Stored as str to avoid pydantic-settings JSON parsing of env vars.
    # Access parsed list via the allowed_origins_list computed field.
    allowed_origins: str = _DEFAULT_ORIGINS

    @field_validator("allowed_origins")
    @classmethod
    def reject_wildcard_origin(cls, v: str) -> str:
        """Reject wildcard CORS origins — unsafe with allow_credentials=True."""
        origins = _parse_origins_str(v)
        if "*" in origins:
            raise ValueError(
                "Wildcard '*' is not allowed in ALLOWED_ORIGINS. "
                "Enumerate specific origins instead."
            )
        return v

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allowed_origins_list(self) -> list[str]:
        """Parsed list of allowed CORS origins."""
        return _parse_origins_str(self.allowed_origins)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ai_gateway_base_url(self) -> str:
        """Cloudflare AI Gateway base URL for OpenAI-compatible calls."""
        if self.cloudflare_account_id and self.cloudflare_gateway_id:
            return (
                f"https://gateway.ai.cloudflare.com/v1/"
                f"{self.cloudflare_account_id}/{self.cloudflare_gateway_id}/openai"
            )
        return "https://openrouter.ai/api/v1"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
