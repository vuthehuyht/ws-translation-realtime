"""Authentication and Identity REST API Endpoints."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request, Response, status
from fastapi.responses import JSONResponse

from app.api.deps import AccessTokenContext, get_auth_service, get_logout_token_context
from app.core.config import get_settings
from app.core.exceptions import (
    ForbiddenException,
    UnauthorizedException,
    build_app_error_response,
)
from app.schemas.requests import (
    ConfirmRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RegisterRequest,
    ResendOtpRequest,
    ResetPasswordRequest,
)
from app.schemas.responses import (
    ConfirmResponse,
    ForgotPasswordResponse,
    LoginResponse,
    RefreshResponse,
    RegisterResponse,
    ResendOtpResponse,
    ResetPasswordResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "ws_refresh_token"
REMEMBER_COOKIE_NAME = "ws_remember_me"
AUTH_COOKIE_PATH = "/api/v1/auth"


def _set_no_store_headers(response: Response) -> None:
    """Prevent shared proxies or browser caches from storing token-issuing responses."""
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


def _set_refresh_cookies(
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


def _clear_refresh_cookies(response: Response) -> None:
    """Expire auth cookies on the response when a refresh token is rejected."""
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


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new host or user account",
)
async def register(
    payload: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> RegisterResponse:
    """Register a new user account in Cognito and trigger OTP email delivery."""
    return await auth_service.register(payload)


@router.post(
    "/confirm",
    response_model=ConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm registration with 6-digit OTP",
)
async def confirm(
    payload: ConfirmRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ConfirmResponse:
    """Verify registration code sent via email and initialize wallet/profile."""
    return await auth_service.confirm_sign_up(payload)


@router.post(
    "/resend-otp",
    response_model=ResendOtpResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend 6-digit registration OTP with 60s cooldown",
)
async def resend_otp(
    payload: ResendOtpRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ResendOtpResponse:
    """Resend confirmation OTP via Cognito with Redis rate limiting."""
    return await auth_service.resend_otp(payload)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Request a 6-digit password reset OTP via email",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ForgotPasswordResponse:
    """Trigger Cognito ForgotPassword OTP delivery with a 3-per-15-minute Redis rate limit."""
    result = await auth_service.forgot_password(payload)
    _set_no_store_headers(response)
    return result


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm password reset with 6-digit OTP and set a new password",
)
async def reset_password(
    payload: ResetPasswordRequest,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ResetPasswordResponse:
    """Confirm Cognito password reset, revoke all active sessions, and clear auth cookies."""
    result = await auth_service.reset_password(payload)
    _set_no_store_headers(response)
    _clear_refresh_cookies(response)
    return result


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT tokens",
)
async def login(
    payload: LoginRequest,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    """Authenticate email and password against Cognito and set HttpOnly refresh cookie."""
    result = await auth_service.login(payload)
    _set_no_store_headers(response)
    _set_refresh_cookies(
        response=response,
        refresh_token=result.refresh_token,
        remember_me=payload.remember_me,
    )
    return result.response


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sign out this device or every device and revoke tokens",
)
async def logout(
    request: Request,
    response: Response,
    context: Annotated[AccessTokenContext, Depends(get_logout_token_context)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    payload: Annotated[LogoutRequest | None, Body()] = None,
) -> None:
    """Revoke the refresh token (or all sessions with `global`) and clear the auth cookies."""
    refresh_token = (request.cookies.get(REFRESH_COOKIE_NAME) or "").strip() or None
    await auth_service.logout(
        access_token=context.token,
        subject=context.subject,
        expires_at=context.expires_at,
        refresh_token=refresh_token,
        global_sign_out=bool(payload and payload.global_sign_out),
        session_id=context.session_id,
    )
    # Cookies are cleared only after revocation succeeded; on a Cognito outage the error
    # response keeps them so the client can retry.
    _clear_refresh_cookies(response)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Silently refresh AccessToken and IdToken using the HttpOnly refresh cookie",
)
async def refresh(
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> RefreshResponse | JSONResponse:
    """Exchange the HttpOnly refresh cookie for fresh AccessToken, IdToken, and user profile."""
    # Cookie-only on purpose: accepting a body token would let a script that obtained the
    # refresh token elsewhere bypass the HttpOnly protection.
    refresh_token = (request.cookies.get(REFRESH_COOKIE_NAME) or "").strip()

    try:
        result = await auth_service.refresh_session(refresh_token)
    except (UnauthorizedException, ForbiddenException) as exc:
        # Attach Set-Cookie deletions directly on the error JSONResponse because FastAPI
        # exception handlers create a new response object and discard prior Response mutations.
        error_response = build_app_error_response(exc)
        _set_no_store_headers(error_response)
        _clear_refresh_cookies(error_response)
        return error_response

    _set_no_store_headers(response)
    if result.refresh_token:
        remember_me = request.cookies.get(REMEMBER_COOKIE_NAME) == "1"
        _set_refresh_cookies(
            response=response,
            refresh_token=result.refresh_token,
            remember_me=remember_me,
        )

    return result.response
