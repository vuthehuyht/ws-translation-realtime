"""API integration tests for POST /api/v1/auth/logout (TASK-AUTH-08)."""

import asyncio
from datetime import timedelta

import fakeredis.aioredis
import pytest
from httpx import AsyncClient
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.exceptions import BadGatewayException
from app.core.security import create_access_token
from app.integrations.cognito import get_cognito_client

REFRESH_COOKIE = "ws_refresh_token"
COOKIE_PATH = "/api/v1/auth"


async def _register_and_login(async_client: AsyncClient, email: str) -> str:
    """Register, confirm and log in; return the access token. The refresh token stays in the jar."""
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123@", "fullName": "Logout Host"},
    )
    await async_client.post(
        "/api/v1/auth/confirm",
        json={"email": email, "otpCode": "123456"},
    )
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
