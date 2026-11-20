"""User Profile, Wallet Summary, Avatar, and Security Response Schemas."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WalletSummaryResponse(BaseModel):
    """Embedded wallet balance & settings summary returned in GET /users/me."""

    balance: Decimal
    auto_degrade_tts: bool = Field(default=True, alias="autoDegradeTts")
    auto_topup_enabled: bool = Field(default=False, alias="autoTopupEnabled")

    model_config = ConfigDict(populate_by_name=True)


class UserMeResponse(BaseModel):
    """Complete authenticated Host profile joined across users, user_profiles, and wallets."""

    id: str
    email: str
    role: str
    status: str
    full_name: str = Field(..., alias="fullName")
    phone_number: str | None = Field(default=None, alias="phoneNumber")
    bio: str | None = None
    avatar_url: str | None = Field(default=None, alias="avatarUrl")
    timezone: str = "Asia/Ho_Chi_Minh"
    default_source_lang: str = Field(default="vi-VN", alias="defaultSourceLang")
    default_target_langs: list[str] = Field(
        default_factory=lambda: ["en-US"], alias="defaultTargetLangs"
    )
    company_name: str | None = Field(default=None, alias="companyName")
    tax_code: str | None = Field(default=None, alias="taxCode")
    company_address: str | None = Field(default=None, alias="companyAddress")
    preferences: dict[str, Any] = Field(default_factory=dict)
    wallet: WalletSummaryResponse | None = None

    model_config = ConfigDict(populate_by_name=True)


class AvatarUploadUrlResponse(BaseModel):
    """Presigned S3 PUT URL payload for direct client avatar uploads."""

    upload_url: str = Field(..., alias="uploadUrl")
    s3_key: str = Field(..., alias="s3Key")
    fields: dict[str, str] = Field(default_factory=dict)
    expires_in: int = Field(default=900, alias="expiresIn")
    max_size_bytes: int = Field(default=2_097_152, alias="maxSizeBytes")

    model_config = ConfigDict(populate_by_name=True)


class AvatarConfirmResponse(BaseModel):
    """Response returned after confirming an uploaded avatar object."""

    avatar_url: str = Field(..., alias="avatarUrl")
    s3_key: str = Field(..., alias="s3Key")

    model_config = ConfigDict(populate_by_name=True)


class ChangePasswordResponse(BaseModel):
    """Response returned after a successful password change."""

    status: str = "PASSWORD_CHANGED"
    message: str = "Password has been changed successfully."
