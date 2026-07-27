# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Application configuration via pydantic-settings."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import SecretStr, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from evermore_llm import GatewayScope

# Resolve .env at the service root (services/retriever/.env)
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

# Default CORS origins for local development
_DEFAULT_ORIGINS = "http://localhost:5173,http://localhost:3000"

# Resolved moderation-availability signal surfaced via /health and startup logs.
ModerationStatus = Literal["gateway_guardrails", "openai_api", "disabled"]


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
    supabase_publishable_key: SecretStr = SecretStr("")
    supabase_secret_key: SecretStr = SecretStr("")
    database_url: SecretStr = SecretStr("")

    # Langfuse
    langfuse_secret_key: SecretStr = SecretStr("")
    langfuse_public_key: str = ""
    langfuse_host: str = "https://us.cloud.langfuse.com"

    # LLM gateway (Cloudflare AI Gateway by default; override llm_gateway_url
    # for any OpenAI-compatible gateway)
    llm_gateway_url: str = ""
    cloudflare_account_id: str = ""
    cloudflare_gateway_id: str = ""
    llm_gateway_token: SecretStr = SecretStr("")
    # Optional per-service scoped tokens. When set, each narrows the blast
    # radius of a leaked token to one traffic class instead of authenticating
    # all gateway traffic; unset scoped fields fall back to the shared
    # llm_gateway_token. See gateway_token_for().
    llm_gateway_token_chat: SecretStr = SecretStr("")
    llm_gateway_token_embeddings: SecretStr = SecretStr("")
    llm_gateway_token_moderation: SecretStr = SecretStr("")
    # Gateway-specific auth header. Isolating the name here keeps the client
    # code generic: a different gateway sets this (or leaves the token empty to
    # use the standard Authorization header).
    llm_gateway_auth_header: str = "cf-aig-authorization"

    # Cloudflare R2 object storage
    r2_account_id: str = ""
    r2_access_key_id: SecretStr = SecretStr("")
    r2_secret_access_key: SecretStr = SecretStr("")
    r2_bucket: str = ""
    r2_endpoint_url: str = ""

    # GCP
    gcp_project_id: str = ""

    # OpenTelemetry
    otel_enabled: bool = True
    otel_trace_sample_rate: float = 1.0
    otel_exporter_otlp_endpoint: str = ""

    # Database
    # Secure by default: production (Supabase / Cloud Run) requires TLS.
    # Local dev opts out via DATABASE_REQUIRE_SSL=false (the local pgvector
    # container on localhost:5433 has no TLS).
    database_require_ssl: bool = True

    # Database connection pool — env-driven so each deployment target (local vs
    # Containers behind Hyperdrive) sizes its own pool without code changes.
    # Defaults preserve prior hardcoded engine behavior.
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: float = 30.0
    db_pool_recycle: int = -1
    db_pool_pre_ping: bool = True

    # LLM
    default_llm_model: str = "anthropic/claude-sonnet-4-6"
    fallback_llm_model: str = "anthropic/claude-haiku-4-5"
    default_embedding_model: str = "openai/text-embedding-3-small"
    llm_timeout_seconds: float = 30.0

    # Safety
    moderation_enabled: bool = True
    # How moderation is enforced when enabled:
    #   "guardrails"  — enforced at the Cloudflare AI Gateway via Guardrails; the
    #                   app does NOT call /moderations (the default gateway does
    #                   not implement that compat endpoint).
    #   "openai_api"  — call the OpenAI-compat /moderations endpoint per request;
    #                   only for gateways that actually implement it.
    moderation_backend: Literal["guardrails", "openai_api"] = "guardrails"

    # Rate limiting (ADR-0012)
    rate_limit_enabled: bool = True
    rate_limit_ask: str = "10/minute"

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

    @property
    def moderation_status(self) -> ModerationStatus:
        """Single source of truth for the visible moderation-availability signal.

        Resolves the configured moderation setup into one of three states,
        surfaced via ``/health`` and startup logs:

        - ``"disabled"`` — moderation is turned off.
        - ``"gateway_guardrails"`` — enforced upstream at the AI Gateway.
        - ``"openai_api"`` — enforced via per-request ``/moderations`` calls.
        """
        if not self.moderation_enabled:
            return "disabled"
        if self.moderation_backend == "guardrails":
            return "gateway_guardrails"
        return "openai_api"

    def gateway_token_for(self, scope: GatewayScope | None) -> SecretStr:
        """Resolve the gateway token to use for a given traffic-class scope.

        Returns the scoped token (llm_gateway_token_chat / _embeddings /
        _moderation) when ``scope`` is given and that scoped field's secret
        value is non-empty; otherwise falls back to the shared
        ``llm_gateway_token``. This lets one leaked scoped token be rotated
        without affecting the other traffic classes, while an unconfigured
        deployment keeps working on the single shared token.

        Args:
            scope: Traffic class needing a token ("chat", "embeddings",
                "moderation"), or None to always use the shared token.

        Returns:
            The resolved SecretStr token to send on the gateway auth header.
        """
        if scope is not None:
            scoped_tokens: dict[GatewayScope, SecretStr] = {
                "chat": self.llm_gateway_token_chat,
                "embeddings": self.llm_gateway_token_embeddings,
                "moderation": self.llm_gateway_token_moderation,
            }
            scoped_token = scoped_tokens[scope]
            if scoped_token.get_secret_value():
                return scoped_token
        return self.llm_gateway_token

    @property
    def llm_gateway_base_url(self) -> str:
        """Base URL for the OpenAI-compatible LLM gateway.

        Resolves an explicit override first so the gateway is swappable to any
        OpenAI-compatible endpoint with config alone; Cloudflare is the default
        concrete provider. The gateway is required: with neither an explicit
        URL nor the Cloudflare IDs configured, this raises rather than routing
        anywhere implicitly.

        This is a plain property (not a computed_field) so it is not evaluated
        during model serialization/dump, where the raise would surface as a
        dump error rather than at the call site that needs a gateway.

        Raises:
            ValueError: If no gateway is configured.
        """
        if self.llm_gateway_url:
            return self.llm_gateway_url
        if self.cloudflare_account_id and self.cloudflare_gateway_id:
            return (
                f"https://gateway.ai.cloudflare.com/v1/"
                f"{self.cloudflare_account_id}/{self.cloudflare_gateway_id}/compat"
            )
        raise ValueError(
            "No LLM gateway configured. Set LLM_GATEWAY_URL, or "
            "CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_GATEWAY_ID."
        )

    @property
    def r2_endpoint(self) -> str:
        """S3-compatible endpoint URL for Cloudflare R2.

        Resolves an explicit override first so the endpoint is swappable with
        config alone; the per-account R2 URL is the default. This is a plain
        property (not a computed_field) so it is not evaluated during model
        serialization, where the raise would surface as a dump error rather than
        at the call site that needs an endpoint.

        Raises:
            ValueError: If neither an endpoint URL nor an account id is set.
        """
        if self.r2_endpoint_url:
            return self.r2_endpoint_url
        if self.r2_account_id:
            return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"
        raise ValueError(
            "No R2 endpoint configured. Set R2_ENDPOINT_URL or R2_ACCOUNT_ID."
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
