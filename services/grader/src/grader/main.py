"""FastAPI application entry point."""

from __future__ import annotations

from typing import Literal

from fast_llms_txt import create_llms_txt_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict

from grader.config import get_settings
from grader.observability.logging import configure_logging
from grader.observability.tracing import traced_span

_VERSION = "0.1.0"


class HealthResponse(BaseModel):
    """Health check response."""

    model_config = ConfigDict(frozen=True)

    status: Literal["healthy"]
    version: str


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(debug=settings.debug)

    app = FastAPI(title="Profile Grader", version=_VERSION)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Health check endpoint. No database to check: grader has no data layer."""
        with traced_span("grader.health_check"):
            return HealthResponse(status="healthy", version=_VERSION)

    # Unauthenticated discovery endpoint at /llms.txt for LLM consumers.
    app.include_router(create_llms_txt_router(app))

    return app


app = create_app()
