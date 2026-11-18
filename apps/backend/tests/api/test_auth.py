"""API integration tests for Auth Endpoints (/api/v1/auth)."""

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


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
    assert "idToken" in login_data["tokens"]
    # Refresh token must only travel in the HttpOnly cookie, never in the JSON body.
    assert "refreshToken" not in login_data["tokens"]
    assert any(
        h.startswith("ws_refresh_token=") for h in login_resp.headers.get_list("set-cookie")
    )
    assert login_data["user"]["email"] == "api.test@example.com"
    assert login_data["user"]["fullName"] == "API Tester"
    assert login_data["user"]["role"] == "HOST"

    # 5. Wrong password returns 401 Unauthorized
    bad_login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "api.test@example.com", "password": "WrongPassword123!"},
    )
    assert bad_login_resp.status_code == 401
    assert bad_login_resp.json()["error"]["code"] == "UNAUTHORIZED"


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

    # Empty password on login -> 422
    empty_pwd_login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": ""},
    )
    assert empty_pwd_login_resp.status_code == 422


async def test_auth_api_login_rejects_unconfirmed_and_suspended_users(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    email = "status.check@example.com"
    password = "Password123@"

    reg_resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "fullName": "Status Checker",
        },
    )
    assert reg_resp.status_code == 201

    # Unconfirmed user cannot log in -> 401
    unconfirmed_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert unconfirmed_resp.status_code == 401
    assert unconfirmed_resp.json()["error"]["code"] == "UNAUTHORIZED"

    # Confirm user, then suspend in PostgreSQL -> 403 FORBIDDEN
    confirm_resp = await async_client.post(
        "/api/v1/auth/confirm",
        json={"email": email, "otpCode": "123456"},
    )
    assert confirm_resp.status_code == 200

    await db_session.execute(
        update(User).where(User.email == email).values(status="SUSPENDED")
    )
    await db_session.commit()

    suspended_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert suspended_resp.status_code == 403
    assert suspended_resp.json()["error"]["code"] == "FORBIDDEN"


async def test_auth_api_refresh_token_cookie_only(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # Register & confirm user
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh.api@example.com",
            "password": "Password123@",
            "fullName": "Refresh API Host",
        },
    )
    await async_client.post(
        "/api/v1/auth/confirm",
        json={"email": "refresh.api@example.com", "otpCode": "123456"},
    )

    # 1. Login with rememberMe=True sets persistent HttpOnly refresh cookie
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "refresh.api@example.com",
            "password": "Password123@",
            "rememberMe": True,
        },
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "refreshToken" not in login_data["tokens"]
    user_id = login_data["user"]["id"]
    set_cookie_headers = login_resp.headers.get_list("set-cookie")
    refresh_cookie_header = next(h for h in set_cookie_headers if h.startswith("ws_refresh_token="))
    refresh_token = refresh_cookie_header.split(";", 1)[0].removeprefix("ws_refresh_token=")
    assert refresh_token
    assert "HttpOnly" in refresh_cookie_header
    assert "Path=/api/v1/auth" in refresh_cookie_header
    assert "Max-Age=" in refresh_cookie_header

    # 2. Refresh via HttpOnly cookie with empty body succeeds
    cookie_refresh_resp = await async_client.post("/api/v1/auth/refresh")
    assert cookie_refresh_resp.status_code == 200
    refreshed_data = cookie_refresh_resp.json()
    assert refreshed_data["tokens"]["accessToken"]
    assert refreshed_data["tokens"]["idToken"]
    assert refreshed_data["user"]["email"] == "refresh.api@example.com"
    assert "refreshToken" not in refreshed_data["tokens"]

    # 3. A body token is ignored: without the cookie the request is rejected even if the
    # body carries a valid refresh token.
    async_client.cookies.clear()
    body_refresh_resp = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": refresh_token},
    )
    assert body_refresh_resp.status_code == 401

    # 4. Missing cookie -> 401
    missing_resp = await async_client.post("/api/v1/auth/refresh", json={})
    assert missing_resp.status_code == 401
    assert missing_resp.json()["error"]["code"] == "UNAUTHORIZED"

    # 5. Invalid cookie token -> 401 and clears cookies
    async_client.cookies.set("ws_refresh_token", "invalid_token", path="/api/v1/auth")
    bad_resp = await async_client.post("/api/v1/auth/refresh")
    assert bad_resp.status_code == 401
    cleared_headers = bad_resp.headers.get_list("set-cookie")
    assert any(h.startswith('ws_refresh_token=""') and "Max-Age=0" in h for h in cleared_headers)

    # 6. Suspended user -> 403 and clears cookies
    await db_session.execute(
        update(User).where(User.id == user_id).values(status="SUSPENDED")
    )
    await db_session.commit()
    async_client.cookies.set("ws_refresh_token", refresh_token, path="/api/v1/auth")
    suspended_resp = await async_client.post("/api/v1/auth/refresh")
    assert suspended_resp.status_code == 403
    assert suspended_resp.json()["error"]["code"] == "FORBIDDEN"
    assert any(
        h.startswith('ws_refresh_token=""') and "Max-Age=0" in h
        for h in suspended_resp.headers.get_list("set-cookie")
    )


async def test_auth_api_session_cookie_without_remember_me_and_token_rotation(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "session.cookie@example.com",
            "password": "Password123@",
            "fullName": "Session Cookie Host",
        },
    )
    await async_client.post(
        "/api/v1/auth/confirm",
        json={"email": "session.cookie@example.com", "otpCode": "123456"},
    )

    # 1. Login with rememberMe=False sets session cookie (no Max-Age)
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "session.cookie@example.com",
            "password": "Password123@",
            "rememberMe": False,
        },
    )
    assert login_resp.status_code == 200
    set_cookie_headers = login_resp.headers.get_list("set-cookie")
    refresh_cookie = next(h for h in set_cookie_headers if h.startswith("ws_refresh_token="))
    assert "HttpOnly" in refresh_cookie
    assert "Max-Age=" not in refresh_cookie
    assert any(
        h.startswith('ws_remember_me=""') and "Max-Age=0" in h
        for h in set_cookie_headers
    )

    # 2. Refresh updates ws_refresh_token cookie when Cognito rotates RefreshToken
    from app.integrations.cognito import get_cognito_client

    cognito = get_cognito_client()
    orig_refresh = cognito.refresh_tokens

    async def rotated_refresh(token: str) -> dict[str, object]:
        result = await orig_refresh(token)
        result["refreshToken"] = "rotated_refresh_token_value"
        return result

    monkeypatch.setattr(cognito, "refresh_tokens", rotated_refresh)
    rotated_resp = await async_client.post("/api/v1/auth/refresh")
    assert rotated_resp.status_code == 200
    assert "refreshToken" not in rotated_resp.json()["tokens"]
    rotated_cookies = rotated_resp.headers.get_list("set-cookie")
    assert any(
        h.startswith("ws_refresh_token=rotated_refresh_token_value")
        for h in rotated_cookies
    )


async def test_auth_api_refresh_rejects_token_without_subject_and_clears_cookies(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.integrations.cognito import get_cognito_client

    async def malformed_refresh(_token: str) -> dict[str, object]:
        return {
            "accessToken": "not-a-jwt",
            "idToken": "also-not-a-jwt",
            "refreshToken": None,
            "expiresIn": 3600,
        }

    monkeypatch.setattr(get_cognito_client(), "refresh_tokens", malformed_refresh)
    async_client.cookies.set("ws_refresh_token", "mock_refresh_any", path="/api/v1/auth")

    resp = await async_client.post("/api/v1/auth/refresh")

    assert resp.status_code == 401
    assert any(
        h.startswith('ws_refresh_token=""') and "Max-Age=0" in h
        for h in resp.headers.get_list("set-cookie")
    )
