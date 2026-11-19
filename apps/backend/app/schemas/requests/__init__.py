"""Request Schemas Package."""

from app.schemas.requests.auth import (
    ConfirmRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RegisterRequest,
    ResendOtpRequest,
    ResetPasswordRequest,
)

__all__ = [
    "ConfirmRequest",
    "ForgotPasswordRequest",
    "LoginRequest",
    "LogoutRequest",
    "RegisterRequest",
    "ResendOtpRequest",
    "ResetPasswordRequest",
]
