# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text

from retriever.config import ModerationStatus, get_settings
from retriever.infrastructure.database.session import _get_factory
from retriever.infrastructure.observability.langfuse import (
    configure_langfuse,
    flush_langfuse,
)
from retriever.infrastructure.observability.logging import configure_logging
from retriever.infrastructure.observability.middleware import (
    ExceptionHandlingMiddleware,
    RequestIdMiddleware,
)
from retriever.infrastructure.observability.tracing import configure_tracing
from retriever.infrastructure.rate_limit import configure_rate_limiting
from retriever.modules.auth import require_subscription
from retriever.modules.documents.routes import router as documents_router
from retriever.modules.messages.routes import router as messages_router
from retriever.modules.rag.routes import router as rag_router

logger = structlog.get_logger(__name__)

health_router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response."""

    model_config = ConfigDict(frozen=True)

    status: Literal["healthy", "degraded"]
    version: str
    database: Literal["connected", "unavailable"]
    pgvector: Literal["available", "unavailable"]
    moderation: ModerationStatus


@health_router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint.

    Checks database connectivity and pgvector extension availability.
    Never raises — returns degraded status on failure.
    """
    db_status: Literal["connected", "unavailable"] = "unavailable"
    pgvector_status: Literal["available", "unavailable"] = "unavailable"

    try:
        session_factory = _get_factory()
        async with session_factory() as session:
            # Check database connectivity
            result = await session.execute(text("SELECT 1"))
            if result.scalar() == 1:
                db_status = "connected"

            # Check pgvector extension
            ext_result = await session.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            )
            if ext_result.scalar() == 1:
                pgvector_status = "available"
    except Exception:
        logger.warning("health_check_db_failed", exc_info=True)

    overall: Literal["healthy", "degraded"] = (
        "healthy"
        if db_status == "connected" and pgvector_status == "available"
        else "degraded"
    )

    # Moderation availability is config-only: never raises, no DB dependency.
    return HealthResponse(
        status=overall,
        version="2.0.0",
        database=db_status,
        pgvector=pgvector_status,
        moderation=get_settings().moderation_status,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan: startup and shutdown."""
    logger = structlog.get_logger(__name__)
    logger.info("retriever.startup")
    logger.info("moderation_configured", mode=get_settings().moderation_status)

    # Wire up DocumentService with RAG pipeline providers
    from retriever.modules.documents.repos import DocumentRepository
    from retriever.modules.documents.routes import configure_document_service
    from retriever.modules.documents.services import DocumentService
    from retriever.modules.rag.dependencies import (
        get_rag_service,
        get_semantic_cache,
        get_session_factory,
        get_vector_store,
    )

    session_factory = get_session_factory()
    doc_repo = DocumentRepository(session_factory)
    doc_service = DocumentService(
        document_repo=doc_repo,
        rag_service=get_rag_service(),
        vector_store=get_vector_store(),
        semantic_cache=get_semantic_cache(),
    )
    configure_document_service(doc_service)
    logger.info("retriever.document_service_configured")

    yield
    flush_langfuse()
    logger.info("retriever.shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(debug=settings.debug)

    app = FastAPI(
        title="Retriever",
        description="AI-powered Q&A system for shelter volunteers",
        version="2.0.0",
        lifespan=lifespan,
    )

    # Tracing must run after app creation so FastAPI can be instrumented
    configure_tracing(
        service_name="retriever",
        debug=settings.debug,
        gcp_project_id=settings.gcp_project_id,
        sample_rate=settings.otel_trace_sample_rate,
        app=app,
        enabled=settings.otel_enabled,
        otlp_endpoint=settings.otel_exporter_otlp_endpoint,
    )

    # Langfuse LLM observability
    configure_langfuse(
        secret_key=settings.langfuse_secret_key.get_secret_value(),
        public_key=settings.langfuse_public_key,
        host=settings.langfuse_host,
    )

    # Exception handling must sit inside CORS so 500 responses are built
    # below the CORS layer and still carry Access-Control-Allow-Origin.
    # Starlette would otherwise route a base-Exception handler to the
    # outermost ServerErrorMiddleware, above CORS, and the browser would
    # block the error. Added first, so it is the innermost user middleware.
    app.add_middleware(ExceptionHandlingMiddleware)

    # Request ID must be added before CORS (outer middleware runs first)
    app.add_middleware(RequestIdMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    # ADR-0012 rate limiting: registered after CORS so a 429 raised inside the
    # router stack still exits back out through the CORS middleware above it
    # and carries Access-Control-Allow-Origin.
    configure_rate_limiting(app)

    # /api/v1 routes require an active "retriever" subscription (claim-based,
    # no DB read — see docs/subscriptions.md). Health has no /api/v1 prefix
    # and stays ungated so orchestrators can probe liveness without a token.
    retriever_subscription = Depends(require_subscription("retriever"))

    app.include_router(health_router)
    app.include_router(messages_router, dependencies=[retriever_subscription])
    app.include_router(documents_router, dependencies=[retriever_subscription])
    app.include_router(rag_router, dependencies=[retriever_subscription])

    return app


app = create_app()
