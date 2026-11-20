"""Shared HTTP cookie and response header helpers for auth-sensitive endpoints."""

from fastapi import Response

from app.core.config import get_settings

REFRESH_COOKIE_NAME = "ws_refresh_token"
REMEMBER_COOKIE_NAME = "ws_remember_me"
AUTH_COOKIE_PATH = "/api/v1/auth"


def set_no_store_headers(response: Response) -> None:
    """Prevent shared proxies or browser caches from storing token-issuing responses."""
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


def set_refresh_cookies(
    response: Response,
    refresh_token: str,
    remember_me: bool,
) -> None:
    """Persist refresh token in an HttpOnly cookie scoped to /api/v1/auth."""
    settings = get_settings()
    secure = settings.app.use_secure_cookies
    max_age = settings.security.refresh_token_expire_days * 86400 if remember_me else None
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age,
        path=AUTH_COOKIE_PATH,
        httponly=True,
        secure=secure,
        samesite="lax",
    )
    if remember_me:
        response.set_cookie(
            key=REMEMBER_COOKIE_NAME,
            value="1",
            max_age=max_age,
            path=AUTH_COOKIE_PATH,
            httponly=True,
            secure=secure,
            samesite="lax",
        )
    else:
        response.delete_cookie(
            key=REMEMBER_COOKIE_NAME,
            path=AUTH_COOKIE_PATH,
            httponly=True,
            secure=secure,
            samesite="lax",
        )


def clear_refresh_cookies(response: Response) -> None:
    """Expire auth cookies on the response when a session is revoked or deleted."""
    settings = get_settings()
    secure = settings.app.use_secure_cookies
    for cookie_name in (REFRESH_COOKIE_NAME, REMEMBER_COOKIE_NAME):
        response.delete_cookie(
            key=cookie_name,
            path=AUTH_COOKIE_PATH,
            httponly=True,
            secure=secure,
            samesite="lax",
        )
