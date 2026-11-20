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
from app.schemas.requests.user import (
    AvatarConfirmRequest,
    AvatarUploadUrlRequest,
    ChangePasswordRequest,
    DeleteAccountRequest,
    UpdateBillingInfoRequest,
    UpdatePreferencesRequest,
    UpdateProfileRequest,
)

__all__ = [
    "AvatarConfirmRequest",
    "AvatarUploadUrlRequest",
    "ChangePasswordRequest",
    "ConfirmRequest",
    "DeleteAccountRequest",
    "ForgotPasswordRequest",
    "LoginRequest",
    "LogoutRequest",
    "RegisterRequest",
    "ResendOtpRequest",
    "ResetPasswordRequest",
    "UpdateBillingInfoRequest",
    "UpdatePreferencesRequest",
    "UpdateProfileRequest",
]
