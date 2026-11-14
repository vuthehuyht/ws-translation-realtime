"""Authentication and Identity REST API Endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service
from app.schemas.requests import (
    ConfirmRequest,
    LoginRequest,
    RegisterRequest,
    ResendOtpRequest,
)
from app.schemas.responses import (
    ConfirmResponse,
    LoginResponse,
    RegisterResponse,
    ResendOtpResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


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
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT tokens",
)
async def login(
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    """Authenticate email and password against Cognito."""
    return await auth_service.login(payload)
