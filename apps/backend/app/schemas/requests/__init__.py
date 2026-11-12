"""Request Schemas Package."""

from app.schemas.requests.auth import (
    ConfirmRequest,
    LoginRequest,
    RegisterRequest,
)

__all__ = [
    "ConfirmRequest",
    "LoginRequest",
    "RegisterRequest",
]
