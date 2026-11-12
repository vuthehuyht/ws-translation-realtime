"""Health Check Response Schema."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Payload for system health and liveness check."""

    status: str
    service: str
    env: str
