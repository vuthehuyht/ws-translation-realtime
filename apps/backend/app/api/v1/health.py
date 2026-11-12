"""Health and Liveness Check REST API Endpoint."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application Health & Liveness Check",
)
async def health_check() -> HealthResponse:
    """Return runtime service health metadata."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        env=settings.env,
    )
