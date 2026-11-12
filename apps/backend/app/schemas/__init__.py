"""Schemas Package.

Exposes domain Request, Response, and WebSocket Protocol schemas.
"""

from app.schemas.requests import (
    ConfirmRequest,
    LoginRequest,
    RegisterRequest,
)
from app.schemas.responses import (
    HealthResponse,
    LoginResponse,
    RegisterResponse,
    TokenResponse,
    UserProfileResponse,
)
from app.schemas.ws_protocol import BinaryAudioFrame

__all__ = [
    "BinaryAudioFrame",
    "ConfirmRequest",
    "HealthResponse",
    "LoginRequest",
    "LoginResponse",
    "RegisterRequest",
    "RegisterResponse",
    "TokenResponse",
    "UserProfileResponse",
]
