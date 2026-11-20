"""Unit tests for shared auth cookie and cache-control helpers (app.api.cookies)."""

from fastapi import Response

from app.api.cookies import (
    AUTH_COOKIE_PATH,
    REFRESH_COOKIE_NAME,
    REMEMBER_COOKIE_NAME,
    clear_refresh_cookies,
    set_no_store_headers,
    set_refresh_cookies,
)


def test_set_no_store_headers_sets_cache_control_and_pragma() -> None:
    response = Response()
    set_no_store_headers(response)
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"


def test_set_and_clear_refresh_cookies() -> None:
    resp_remember = Response()
    set_refresh_cookies(resp_remember, refresh_token="rt-123", remember_me=True)
    set_cookies_remember = " ".join(resp_remember.headers.getlist("set-cookie"))
    assert f"{REFRESH_COOKIE_NAME}=rt-123" in set_cookies_remember
    assert f"{REMEMBER_COOKIE_NAME}=1" in set_cookies_remember
    assert f"Path={AUTH_COOKIE_PATH}" in set_cookies_remember
    assert "HttpOnly" in set_cookies_remember

    resp_session = Response()
    set_refresh_cookies(resp_session, refresh_token="rt-456", remember_me=False)
    set_cookies_session = " ".join(resp_session.headers.getlist("set-cookie"))
    assert f"{REFRESH_COOKIE_NAME}=rt-456" in set_cookies_session
    assert f'{REMEMBER_COOKIE_NAME}=""' in set_cookies_session

    resp_clear = Response()
    clear_refresh_cookies(resp_clear)
    cleared = " ".join(resp_clear.headers.getlist("set-cookie"))
    assert f'{REFRESH_COOKIE_NAME}=""' in cleared
    assert f'{REMEMBER_COOKIE_NAME}=""' in cleared
