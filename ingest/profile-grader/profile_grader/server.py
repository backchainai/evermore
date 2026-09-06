"""Local dashboard server: a thin JSON API over the scored records plus the static view.

The API is the durable contract (shapes defined in `schema.py`, used as `response_model`
so they are validated and documented at `/api/docs`). When profile-grader folds into the
Evermore platform these routes port into a `services/` module and the static view is
rebuilt in SvelteKit against the same shapes:

    GET /                    -> the interactive dashboard (static single-file HTML)
    GET /api/index           -> cohort table + rubric dimensions + band legend
    GET /api/profile/{slug}  -> one self-contained per-profile record

Data access goes through a `Store` (below), injected into `create_app`. The default
`FileStore` reads the JSON files `grade score` wrote; the platform swaps in a
Supabase-backed store without touching the routes. Nothing here scores or scrapes.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Protocol

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .record import RESERVED_SLUGS
from .schema import IndexResponse, ProfileRecord

_STATIC = Path(__file__).resolve().parent / "dashboard"
# FOHA slug shape: lowercase alnum with internal hyphens. Also the path-traversal guard.
_SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]*")


class Store(Protocol):
    """Read side of the scored data. The platform port swaps FileStore for a DB store."""

    def get_index(self) -> dict | None: ...
    def get_record(self, slug: str) -> dict | None: ...


class FileStore:
    """Serve records straight off the results directory `grade score` wrote."""

    def __init__(self, results_dir: Path) -> None:
        self.results_dir = results_dir

    def get_index(self) -> dict | None:
        p = self.results_dir / "index.json"
        return json.loads(p.read_text()) if p.is_file() else None

    def get_record(self, slug: str) -> dict | None:
        p = self.results_dir / f"{slug}.json"
        return json.loads(p.read_text()) if p.is_file() else None


def create_app(store: Store, cors_origins: list[str] | None = None) -> FastAPI:
    """Build the dashboard app over an injected data store.

    cors_origins: browser origins allowed to call the API. Defaults to any origin
    (GET-only, read-only public data) so the SvelteKit dev server works out of the box.
    """
    app = FastAPI(title="Profile Grader Dashboard", docs_url="/api/docs")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins is not None else ["*"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.get("/api/index", response_model=IndexResponse)
    def api_index() -> dict:
        data = store.get_index()
        if data is None:
            raise HTTPException(404, "No index found. Run `grade score` to generate records.")
        return data

    @app.get("/api/profile/{slug}", response_model=ProfileRecord)
    def api_profile(slug: str) -> dict:
        if not _SLUG_RE.fullmatch(slug) or slug in RESERVED_SLUGS:
            raise HTTPException(400, "Invalid slug.")
        data = store.get_record(slug)
        if data is None:
            raise HTTPException(404, f"No record for '{slug}'.")
        return data

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(_STATIC / "index.html")

    return app


def create_file_app(results_dir: Path, cors_origins: list[str] | None = None) -> FastAPI:
    return create_app(FileStore(results_dir), cors_origins=cors_origins)


def serve(results_dir: Path, host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the dashboard with uvicorn (blocking)."""
    import uvicorn

    uvicorn.run(create_file_app(results_dir), host=host, port=port)
