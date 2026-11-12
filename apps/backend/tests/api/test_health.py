"""API integration tests for Health & Liveness Endpoints."""

from httpx import AsyncClient


async def test_health_endpoint_returns_ok(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "ws-translation-backend"
