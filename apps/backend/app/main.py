"""FastAPI Backend Application Entrypoint.

Configures application lifecycle, CORS, RFC 7807 exception handlers,
and registers REST API and WebSocket routes.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.core.config import get_settings
from app.core.db import close_db_connections
from app.core.exceptions import register_exception_handlers

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan startup and teardown routines."""
    settings = get_settings()
    logger.info("Starting up %s in '%s' environment", settings.app_name, settings.env)
    yield
    logger.info("Shutting down %s, disposing database connection pools...", settings.app_name)
    await close_db_connections()


def create_app() -> FastAPI:
    """Application factory for FastAPI instance."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS Middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register standardized RFC 7807 exception handlers
    register_exception_handlers(application)

    # API Routers
    application.include_router(health_router, prefix="/api/v1")
    application.include_router(auth_router, prefix="/api/v1")

    return application


app = create_app()
