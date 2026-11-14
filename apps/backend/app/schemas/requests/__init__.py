"""Request Schemas Package."""

from app.schemas.requests.auth import (
    ConfirmRequest,
    LoginRequest,
    RegisterRequest,
    ResendOtpRequest,
)

__all__ = [
    "ConfirmRequest",
    "LoginRequest",
    "RegisterRequest",
    "ResendOtpRequest",
]
