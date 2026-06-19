"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
from typing import Literal

import structlog
from fast_llms_txt import create_llms_txt_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict

from petdata.config import get_settings
from petdata.modules.db import Database, init_database, migrate
from petdata.modules.web.routes import router as web_router

logger = structlog.get_logger(__name__)


class HealthResponse(BaseModel):
    """Health check response."""

    model_config = ConfigDict(frozen=True)

    status: Literal["healthy", "degraded"]
    version: str
    database: Literal["connected", "unavailable"]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Pet Data",
        description="Behavioral observations and adoption data",
        version="1.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Initialize database
    db_path = settings.database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    init_database(db_path)
    migrate(db_path)
    db = Database(db_path)

    # Store db on app state for dependency injection
    app.state.db = db

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Health check endpoint."""
        db_status: Literal["connected", "unavailable"] = "unavailable"
        try:
            # Verify database is accessible
            animals = await asyncio.to_thread(db.list_animals, 1, 0)
            _ = animals  # just need the call to succeed
            db_status = "connected"
        except Exception:
            logger.warning("health_check_db_failed", exc_info=True)

        return HealthResponse(
            status="healthy" if db_status == "connected" else "degraded",
            version="1.1.0",
            database=db_status,
        )

    app.include_router(web_router, prefix="/api/v1")
    # Unauthenticated discovery endpoint at /llms.txt for LLM consumers.
    app.include_router(create_llms_txt_router(app))

    return app


app = create_app()
