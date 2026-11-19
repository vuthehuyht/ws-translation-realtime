"""API integration tests for Auth Endpoints (/api/v1/auth)."""

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock

import fakeredis.aioredis
import pytest
from httpx import AsyncClient
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadGatewayException
from app.core.security import create_access_token
from app.integrations.cognito import get_cognito_client
from app.models.user import User
from app.repositories.user_repository import UserRepository

REFRESH_COOKIE = "ws_refresh_token"
COOKIE_PATH = "/api/v1/auth"


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
    assert reg_data.get("userSub") is None

    # 2. Duplicate registration returns 409 Conflict with RESOURCE_CONFLICT error code
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
    assert confirm_data == {"status": "CONFIRMED"}

    # Confirm with wrong OTP fails even after user is already confirmed
    wrong_after_confirm = await async_client.post(
        "/api/v1/auth/confirm",
        json={"email": "api.test@example.com", "otpCode": "000000"},
    )
    assert wrong_after_confirm.status_code == 422

    # Idempotent second confirmation with valid code returns 200 without exposing balance/sub
    confirm_resp_2 = await async_client.post("/api/v1/auth/confirm", json=confirm_payload)
    assert confirm_resp_2.status_code == 200
    assert confirm_resp_2.json() == {"status": "CONFIRMED"}

    # 4. Login after confirmation
    login_payload = {
        "email": "api.test@example.com",
        "password": "Password123@",
    }
    login_resp = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    assert login_resp.headers.get("cache-control") == "no-store"
    assert login_resp.headers.get("pragma") == "no-cache"
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

    # Confirm with unknown email -> uniform 422 (prevents email enumeration)
    unknown_confirm_resp = await async_client.post(
        "/api/v1/auth/confirm",
        json={"email": "nobody@example.com", "otpCode": "123456"},
    )
    assert unknown_confirm_resp.status_code == 422

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

    # Resend OTP for unknown email -> uniform 200 OTP_SENT (prevents email enumeration)
    unknown_resend_resp = await async_client.post(
        "/api/v1/auth/resend-otp",
        json={"email": "nobody@example.com"},
    )
    assert unknown_resend_resp.status_code == 200
    assert unknown_resend_resp.json()["status"] == "OTP_SENT"

    # Password over max_length (128) -> 422
    too_long_pwd_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "A" * 129},
    )
    assert too_long_pwd_resp.status_code == 422

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
    assert cookie_refresh_resp.headers.get("cache-control") == "no-store"
    assert cookie_refresh_resp.headers.get("pragma") == "no-cache"
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
    assert resp.headers.get("cache-control") == "no-store"
    assert any(
        h.startswith('ws_refresh_token=""') and "Max-Age=0" in h
        for h in resp.headers.get_list("set-cookie")
    )


async def _register_and_confirm(async_client: AsyncClient, email: str) -> None:
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123@", "fullName": "Auth Host"},
    )
    assert reg.status_code == 201
    confirm = await async_client.post(
        "/api/v1/auth/confirm",
        json={"email": email, "otpCode": "123456"},
    )
    assert confirm.status_code == 200


async def _register_and_login(async_client: AsyncClient, email: str) -> str:
    """Register, confirm and log in; return the access token. The refresh token stays in the jar."""
    await _register_and_confirm(async_client, email)
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123@", "rememberMe": True},
    )
    assert login_resp.status_code == 200
    return str(login_resp.json()["tokens"]["accessToken"])


def _expired_token_for(subject: str) -> str:
    return create_access_token(subject=subject, expires_delta=timedelta(seconds=-60))


async def test_logout_clears_cookies_and_blocks_access_token_reuse(
    async_client: AsyncClient,
) -> None:
    access_token = await _register_and_login(async_client, "logout.single@example.com")
    auth_header = {"Authorization": f"Bearer {access_token}"}

    # Logout without a Bearer token is rejected
    assert (await async_client.post("/api/v1/auth/logout")).status_code == 401

    logout_resp = await async_client.post("/api/v1/auth/logout", headers=auth_header)
    assert logout_resp.status_code == 204
    cleared = logout_resp.headers.get_list("set-cookie")
    for name in (REFRESH_COOKIE, "ws_remember_me"):
        assert any(h.startswith(f'{name}=""') and "Max-Age=0" in h for h in cleared)

    # AC: the revoked access token can no longer call authenticated endpoints
    reuse_resp = await async_client.post("/api/v1/auth/logout", headers=auth_header)
    assert reuse_resp.status_code == 401
    assert "revoked" in reuse_resp.json()["error"]["message"]


async def test_logout_revokes_refresh_token_so_replay_fails(
    async_client: AsyncClient,
) -> None:
    access_token = await _register_and_login(async_client, "logout.replay@example.com")
    saved_refresh = async_client.cookies.get(REFRESH_COOKIE, path=COOKIE_PATH)
    assert saved_refresh

    logout_resp = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_resp.status_code == 204

    # An attacker replaying the previously captured cookie must be rejected by Cognito
    async_client.cookies.set(REFRESH_COOKIE, saved_refresh, path=COOKIE_PATH)
    assert (await async_client.post("/api/v1/auth/refresh")).status_code == 401


async def test_logout_with_expired_access_token_still_revokes_refresh_token(
    async_client: AsyncClient,
) -> None:
    access_token = await _register_and_login(async_client, "logout.expired@example.com")
    saved_refresh = async_client.cookies.get(REFRESH_COOKIE, path=COOKIE_PATH)
    assert saved_refresh
    subject = (await async_client.post("/api/v1/auth/refresh")).json()["user"]["id"]
    assert access_token

    # A stale tab holds an expired access token but a live refresh cookie
    resp = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {_expired_token_for(subject)}"},
    )
    assert resp.status_code == 204
    assert any(
        h.startswith(f'{REFRESH_COOKIE}=""') and "Max-Age=0" in h
        for h in resp.headers.get_list("set-cookie")
    )

    # The refresh token itself was revoked at Cognito, not just dropped from the jar
    async_client.cookies.set(REFRESH_COOKIE, saved_refresh, path=COOKIE_PATH)
    assert (await async_client.post("/api/v1/auth/refresh")).status_code == 401


async def test_global_logout_with_expired_access_token_asks_client_to_refresh(
    async_client: AsyncClient,
) -> None:
    await _register_and_login(async_client, "logout.global.expired@example.com")
    subject = (await async_client.post("/api/v1/auth/refresh")).json()["user"]["id"]

    resp = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {_expired_token_for(subject)}"},
        json={"global": True},
    )

    # GlobalSignOut needs a live token, so nothing is half-done and the cookie is kept
    assert resp.status_code == 401
    assert not any(h.startswith(f"{REFRESH_COOKIE}=") for h in resp.headers.get_list("set-cookie"))


async def test_global_logout_revokes_every_device(async_client: AsyncClient) -> None:
    email = "logout.global@example.com"
    device_a_token = await _register_and_login(async_client, email)
    device_a_refresh = async_client.cookies.get(REFRESH_COOKIE, path=COOKIE_PATH)
    assert device_a_refresh

    login_b = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123@"},
    )
    device_b_token = login_b.json()["tokens"]["accessToken"]

    resp = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {device_b_token}"},
        json={"global": True},
    )
    assert resp.status_code == 204

    stale = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {device_a_token}"},
    )
    assert stale.status_code == 401
    async_client.cookies.set(REFRESH_COOKIE, device_a_refresh, path=COOKIE_PATH)
    assert (await async_client.post("/api/v1/auth/refresh")).status_code == 401

    # `iat` has one-second resolution, so a token issued in the same second as the sign-out is
    # treated as older. Wait once so the fresh login is unambiguously newer.
    await asyncio.sleep(1.1)
    relogin = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123@"},
    )
    assert relogin.status_code == 200
    fresh_logout = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {relogin.json()['tokens']['accessToken']}"},
    )
    assert fresh_logout.status_code == 204


async def test_logout_keeps_session_when_cognito_is_down(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    access_token = await _register_and_login(async_client, "logout.outage@example.com")
    auth_header = {"Authorization": f"Bearer {access_token}"}

    async def failing_revoke(_token: str) -> None:
        raise BadGatewayException("Authentication provider error")

    monkeypatch.setattr(get_cognito_client(), "revoke_token", failing_revoke)

    resp = await async_client.post("/api/v1/auth/logout", headers=auth_header)
    assert resp.status_code == 502
    assert not any(h.startswith(f"{REFRESH_COOKIE}=") for h in resp.headers.get_list("set-cookie"))

    # Nothing was revoked locally, so the client can retry once Cognito recovers
    monkeypatch.undo()
    retry = await async_client.post("/api/v1/auth/logout", headers=auth_header)
    assert retry.status_code == 204


async def test_authentication_fails_closed_when_session_store_is_down(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    access_token = await _register_and_login(async_client, "logout.redis@example.com")

    async def broken(*_args: object, **_kwargs: object) -> None:
        raise RedisConnectionError("redis down")

    monkeypatch.setattr(fakeredis.aioredis.FakeRedis, "exists", broken)

    resp = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


async def test_logout_revokes_earlier_access_tokens_of_the_same_session(
    async_client: AsyncClient,
) -> None:
    first_token = await _register_and_login(async_client, "logout.session@example.com")
    refreshed = await async_client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    second_token = refreshed.json()["tokens"]["accessToken"]
    assert second_token != first_token

    # Logging out with the newer token must also kill the older, still-unexpired one
    logout_resp = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {second_token}"},
    )
    assert logout_resp.status_code == 204

    stale = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {first_token}"},
    )
    assert stale.status_code == 401
    assert "revoked" in stale.json()["error"]["message"]


async def test_logout_rejects_malformed_or_foreign_signed_tokens(
    async_client: AsyncClient,
) -> None:
    for bad_token in ("not-a-jwt", "aaa.bbb.ccc"):
        resp = await async_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {bad_token}"},
        )
        assert resp.status_code == 401
        assert not any(
            h.startswith(f"{REFRESH_COOKIE}=") for h in resp.headers.get_list("set-cookie")
        )


async def test_forgot_password_endpoint_happy_path_and_headers(
    async_client: AsyncClient,
) -> None:
    email = "forgot.active@example.com"
    await _register_and_confirm(async_client, email)

    resp = await async_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "  FORGOT.Active@Example.com  "},
    )

    assert resp.status_code == 200
    assert resp.headers.get("cache-control") == "no-store"
    body = resp.json()
    assert body["status"] == "OTP_SENT"
    assert body["email"] == email
    assert "password reset code" in body["message"].lower()


async def test_forgot_password_endpoint_validates_email_format(
    async_client: AsyncClient,
) -> None:
    resp = await async_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "invalid-email"},
    )
    assert resp.status_code == 422


async def test_forgot_password_endpoint_anti_enumeration_unknown_and_suspended(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    unknown_resp = await async_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nobody@example.com"},
    )
    assert unknown_resp.status_code == 200
    assert unknown_resp.json()["status"] == "OTP_SENT"

    suspended_email = "suspended.api@example.com"
    await _register_and_confirm(async_client, suspended_email)
    user_repo = UserRepository(db_session)
    user = await user_repo.get_by_email(suspended_email)
    assert user is not None
    user.status = "SUSPENDED"
    await user_repo.update(user)

    susp_resp = await async_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": suspended_email},
    )
    assert susp_resp.status_code == 200
    assert susp_resp.json()["status"] == "OTP_SENT"


async def test_forgot_password_endpoint_rate_limit_3_per_15_minutes(
    async_client: AsyncClient,
) -> None:
    email = "ratelimit.api@example.com"
    await _register_and_confirm(async_client, email)

    for _ in range(3):
        resp = await async_client.post("/api/v1/auth/forgot-password", json={"email": email})
        assert resp.status_code == 200

    blocked = await async_client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert blocked.status_code == 429
    err = blocked.json()["error"]
    assert err["code"] == "RATE_LIMIT_EXCEEDED"
    assert 1 <= err["details"]["retryAfter"] <= 900


async def test_forgot_password_endpoint_cognito_5xx_returns_502_and_does_not_burn_quota(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    email = "provider.fail@example.com"
    await _register_and_confirm(async_client, email)
    cognito = get_cognito_client()
    monkeypatch.setattr(
        cognito,
        "forgot_password",
        AsyncMock(side_effect=BadGatewayException("Provider down")),
    )

    fail_resp = await async_client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert fail_resp.status_code == 502

    # Restore and verify all 3 attempts are still available
    monkeypatch.undo()
    for _ in range(3):
        ok_resp = await async_client.post("/api/v1/auth/forgot-password", json={"email": email})
        assert ok_resp.status_code == 200


async def test_reset_password_full_flow_revokes_all_sessions(async_client: AsyncClient) -> None:
    email = "reset.flow@example.com"
    old_password = "Password123@"
    new_password = "NewPassword2@"

    await _register_and_confirm(async_client, email)

    # Login to establish an active session (access token + HttpOnly refresh cookie)
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": old_password, "rememberMe": True},
    )
    assert login_resp.status_code == 200
    old_access_token = login_resp.json()["tokens"]["accessToken"]
    old_refresh_cookie = login_resp.cookies.get(REFRESH_COOKIE)
    assert old_refresh_cookie

    # Request reset OTP
    fp_resp = await async_client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert fp_resp.status_code == 200

    # Confirm reset password
    reset_resp = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"email": email, "otpCode": "123456", "newPassword": new_password},
    )
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "PASSWORD_RESET"
    assert reset_resp.headers.get("cache-control") == "no-store"
    set_cookies = reset_resp.headers.get_list("set-cookie")
    assert any(f"{REFRESH_COOKIE}=" in sc and "Max-Age=0" in sc for sc in set_cookies)

    # Old password is rejected
    old_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": old_password},
    )
    assert old_login.status_code == 401

    # Old refresh cookie was revoked by admin_global_sign_out
    async_client.cookies.set(REFRESH_COOKIE, old_refresh_cookie, path=COOKIE_PATH)
    refresh_resp = await async_client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 401

    # Old access token was revoked in Redis blocklist
    logout_with_old = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {old_access_token}"},
    )
    assert logout_with_old.status_code == 401
    assert "revoked" in logout_with_old.text.lower()

    # Replaying the same OTP fails
    replay_resp = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"email": email, "otpCode": "123456", "newPassword": "AnotherPassword3#"},
    )
    assert replay_resp.status_code == 422

    # New password works
    new_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": new_password},
    )
    assert new_login.status_code == 200


async def test_reset_password_invalid_otp_and_weak_password(async_client: AsyncClient) -> None:
    email = "reset.invalid@example.com"
    await _register_and_confirm(async_client, email)
    await async_client.post("/api/v1/auth/forgot-password", json={"email": email})

    wrong_otp = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"email": email, "otpCode": "000000", "newPassword": "NewPassword2@"},
    )
    assert wrong_otp.status_code == 422

    weak_pw = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"email": email, "otpCode": "123456", "newPassword": "NewPassword2"},
    )
    assert weak_pw.status_code == 422


async def test_reset_password_locks_out_after_5_failed_otp_attempts(
    async_client: AsyncClient,
) -> None:
    email = "reset.bruteforce@example.com"
    await _register_and_confirm(async_client, email)
    await async_client.post("/api/v1/auth/forgot-password", json={"email": email})

    for _ in range(5):
        wrong = await async_client.post(
            "/api/v1/auth/reset-password",
            json={"email": email, "otpCode": "000000", "newPassword": "NewPassword2@"},
        )
        assert wrong.status_code == 422

    # Even the correct OTP is rejected until the window expires.
    locked = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"email": email, "otpCode": "123456", "newPassword": "NewPassword2@"},
    )
    assert locked.status_code == 429
    assert 1 <= locked.json()["error"]["details"]["retryAfter"] <= 900


async def test_reset_password_succeeds_when_global_sign_out_fails(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    email = "reset.signout.fail@example.com"
    await _register_and_confirm(async_client, email)
    await async_client.post("/api/v1/auth/forgot-password", json={"email": email})
    monkeypatch.setattr(
        get_cognito_client(),
        "admin_global_sign_out",
        AsyncMock(side_effect=BadGatewayException("Provider down")),
    )

    resp = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"email": email, "otpCode": "123456", "newPassword": "NewPassword2@"},
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "PASSWORD_RESET"


async def test_reset_password_blocks_suspended_account(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    email = "reset.suspended@example.com"
    await _register_and_confirm(async_client, email)
    await async_client.post("/api/v1/auth/forgot-password", json={"email": email})

    await db_session.execute(update(User).where(User.email == email).values(status="SUSPENDED"))
    await db_session.commit()

    resp = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"email": email, "otpCode": "123456", "newPassword": "NewPassword2@"},
    )
    assert resp.status_code == 422
