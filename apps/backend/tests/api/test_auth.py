"""API integration tests for Auth Endpoints (/api/v1/auth)."""

from httpx import AsyncClient


async def test_auth_api_full_registration_and_login_flow(async_client: AsyncClient) -> None:
    # 1. Register (TASK-AUTH-01)
    reg_payload = {
        "email": "api.test@example.com",
        "password": "Password123@",
        "fullName": "API Tester",
        "role": "HOST",
    }
    reg_resp = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert reg_data["email"] == "api.test@example.com"
    assert reg_data["status"] == "CONFIRMATION_REQUIRED"
    assert "userSub" in reg_data
    assert len(reg_data["userSub"]) > 10

    # 2. Duplicate registration returns 409 Conflict
    dup_resp = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_resp.status_code == 409
    assert dup_resp.json()["error"]["code"] == "RESOURCE_CONFLICT"

    # 2b. Resend OTP succeeds (200) and immediate retry is rate-limited (429)
    resend_resp = await async_client.post(
        "/api/v1/auth/resend-otp",
        json={"email": "api.test@example.com"},
    )
    assert resend_resp.status_code == 200
    assert resend_resp.json()["status"] == "OTP_SENT"
    assert resend_resp.json()["retryAfter"] == 60

    resend_spam_resp = await async_client.post(
        "/api/v1/auth/resend-otp",
        json={"email": "api.test@example.com"},
    )
    assert resend_spam_resp.status_code == 429
    assert resend_spam_resp.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    # 3. Confirm with valid code using otpCode alias (TASK-AUTH-02)
    confirm_payload = {
        "email": "api.test@example.com",
        "otpCode": "123456",
    }
    confirm_resp = await async_client.post("/api/v1/auth/confirm", json=confirm_payload)
    assert confirm_resp.status_code == 200
    confirm_data = confirm_resp.json()
    assert confirm_data["status"] == "CONFIRMED"
    assert confirm_data["walletBalance"] == "2.0000"

    # Idempotent second confirmation returns 200 without duplicate key error
    confirm_resp_2 = await async_client.post("/api/v1/auth/confirm", json=confirm_payload)
    assert confirm_resp_2.status_code == 200
    assert confirm_resp_2.json()["walletBalance"] == "2.0000"

    # 4. Login after confirmation
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
    # Invalid email format
    invalid_email_resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "ValidPassword123@",
            "fullName": "Tester",
        },
    )
    assert invalid_email_resp.status_code == 422

    # Weak password - missing special character
    weak_pwd_resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "Password123",
            "fullName": "Tester",
        },
    )
    assert weak_pwd_resp.status_code == 422

    # Weak password - missing uppercase
    no_upper_resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak2@example.com",
            "password": "password123@",
            "fullName": "Tester",
        },
    )
    assert no_upper_resp.status_code == 422

    # Confirm with unknown email -> 404
    unknown_confirm_resp = await async_client.post(
        "/api/v1/auth/confirm",
        json={"email": "nobody@example.com", "otpCode": "123456"},
    )
    assert unknown_confirm_resp.status_code == 404

    # Register a user then confirm with wrong OTP -> 422
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong.otp@example.com",
            "password": "ValidPassword123@",
            "fullName": "Wrong OTP User",
        },
    )
    wrong_otp_resp = await async_client.post(
        "/api/v1/auth/confirm",
        json={"email": "wrong.otp@example.com", "otpCode": "000000"},
    )
    assert wrong_otp_resp.status_code == 422

    # Resend OTP for unknown email -> 404
    unknown_resend_resp = await async_client.post(
        "/api/v1/auth/resend-otp",
        json={"email": "nobody@example.com"},
    )
    assert unknown_resend_resp.status_code == 404
