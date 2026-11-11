from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
    )
    application.include_router(health_router, prefix="/api/v1")
    return application


app = create_app()
