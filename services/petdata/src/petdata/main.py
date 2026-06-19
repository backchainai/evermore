"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Literal

import structlog
from fast_llms_txt import create_llms_txt_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text

from petdata.config import get_settings
from petdata.infrastructure.database.session import _get_factory
from petdata.modules.web.routes import router as web_router

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = structlog.get_logger(__name__)

_VERSION = "1.1.0"


class HealthResponse(BaseModel):
    """Health check response."""

    model_config = ConfigDict(frozen=True)

    status: Literal["healthy", "degraded"]
    version: str
    database: Literal["connected", "unavailable"]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan. Schema is owned by Alembic, not the app."""
    logger.info("petdata.startup")
    yield
    logger.info("petdata.shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Pet Data",
        description="Behavioral observations and adoption data",
        version=_VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Health check endpoint. Verifies database connectivity."""
        db_status: Literal["connected", "unavailable"] = "unavailable"
        try:
            async with _get_factory()() as session:
                result = await session.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    db_status = "connected"
        except Exception:
            logger.warning("health_check_db_failed", exc_info=True)

        return HealthResponse(
            status="healthy" if db_status == "connected" else "degraded",
            version=_VERSION,
            database=db_status,
        )

    app.include_router(web_router, prefix="/api/v1")
    # Unauthenticated discovery endpoint at /llms.txt for LLM consumers.
    app.include_router(create_llms_txt_router(app))

    return app


app = create_app()
