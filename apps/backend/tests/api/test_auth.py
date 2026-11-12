"""API integration tests for Auth Endpoints (/api/v1/auth)."""

from httpx import AsyncClient


async def test_auth_api_full_registration_and_login_flow(async_client: AsyncClient) -> None:
    # 1. Register
    reg_payload = {
        "email": "api.test@example.com",
        "password": "Password123@",
        "full_name": "API Tester",
        "role": "HOST",
    }
    reg_resp = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert reg_data["email"] == "api.test@example.com"
    assert reg_data["status"] == "PENDING_CONFIRMATION"
    assert "userId" in reg_data

    # 2. Duplicate registration returns 409 Conflict
    dup_resp = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_resp.status_code == 409
    assert dup_resp.json()["error"]["code"] == "RESOURCE_CONFLICT"

    # 3. Confirm with valid code
    confirm_payload = {
        "email": "api.test@example.com",
        "confirmation_code": "123456",
    }
    confirm_resp = await async_client.post("/api/v1/auth/confirm", json=confirm_payload)
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "CONFIRMED"

    # 4. Login
    login_payload = {
        "email": "api.test@example.com",
        "password": "Password123@",
    }
    login_resp = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "tokens" in login_data
    assert "accessToken" in login_data["tokens"]
    assert login_data["user"]["email"] == "api.test@example.com"
    assert login_data["user"]["fullName"] == "API Tester"
    assert login_data["user"]["role"] == "HOST"


async def test_auth_api_validation_errors(async_client: AsyncClient) -> None:
    # Invalid email and short password
    invalid_payload = {
        "email": "not-an-email",
        "password": "short",
        "full_name": "T",
    }
    resp = await async_client.post("/api/v1/auth/register", json=invalid_payload)
    assert resp.status_code == 422
