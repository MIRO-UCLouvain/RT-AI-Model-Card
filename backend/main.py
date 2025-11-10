"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.router import api_v1_router
from config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Startup: log configuration summary (DB host masked for safety).
    Shutdown: nothing to clean up at this stage.
    """
    # Mask credentials in the logged URL for safety
    safe_url = settings.DATABASE_URL.split("@")[-1]
    logger.info("Backend starting — database host: %s", safe_url)
    logger.info("Debug mode: %s", settings.DEBUG)
    yield
    logger.info("Backend shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="RT-ModelCard API",
        description=(
            "Backend API for the RT-ModelCard writing tool. "
            "Provides persistence, versioning, comparison, and AI features "
            "for radiotherapy AI model cards."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS — allow the Streamlit frontend and any configured origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Versioned API router
    app.include_router(api_v1_router)

    # Health check — intentionally outside /v1 so monitoring tools
    # and docker healthchecks can reach it without version coupling
    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    return app


app = create_app()
