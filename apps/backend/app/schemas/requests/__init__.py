"""Request Schemas Package."""

from app.schemas.requests.auth import (
    ConfirmRequest,
    LoginRequest,
    LogoutRequest,
    RegisterRequest,
    ResendOtpRequest,
)

__all__ = [
    "ConfirmRequest",
    "LoginRequest",
    "LogoutRequest",
    "RegisterRequest",
    "ResendOtpRequest",
]
