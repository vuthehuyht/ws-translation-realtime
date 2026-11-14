"""Authentication Response Schemas."""

from decimal import Decimal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class RegisterResponse(BaseModel):
    """Response returned upon successful registration."""

    status: str = "CONFIRMATION_REQUIRED"
    email: str
    user_sub: str = Field(
        ...,
        validation_alias=AliasChoices("userSub", "userId", "user_sub", "user_id"),
        serialization_alias="userSub",
    )

    model_config = ConfigDict(populate_by_name=True)

    @property
    def user_id(self) -> str:
        """Alias for backward compatibility."""
        return self.user_sub


class ConfirmResponse(BaseModel):
    """Response returned upon OTP confirmation and wallet initialization."""

    status: str = "CONFIRMED"
    user_sub: str = Field(..., alias="userSub")
    wallet_balance: Decimal = Field(..., alias="walletBalance")
    currency: str = "USD"

    model_config = ConfigDict(populate_by_name=True)


class TokenResponse(BaseModel):
    """Authentication tokens returned by Cognito."""

    access_token: str = Field(..., alias="accessToken")
    id_token: str = Field(..., alias="idToken")
    refresh_token: str = Field(..., alias="refreshToken")
    expires_in: int = Field(default=3600, alias="expiresIn")
    token_type: str = Field(default="Bearer", alias="tokenType")

    model_config = ConfigDict(populate_by_name=True)


class UserProfileResponse(BaseModel):
    """User profile details response."""

    id: str
    email: str
    role: str
    status: str
    full_name: str | None = Field(default=None, alias="fullName")
    default_source_lang: str | None = Field(default="vi-VN", alias="defaultSourceLang")
    default_target_langs: list[str] = Field(default_factory=list, alias="defaultTargetLangs")
    timezone: str = "Asia/Ho_Chi_Minh"

    model_config = ConfigDict(populate_by_name=True)


class LoginResponse(BaseModel):
    """Response on successful login including tokens and user metadata."""

    tokens: TokenResponse
    user: UserProfileResponse


class ResendOtpResponse(BaseModel):
    """Response returned upon successfully resending a confirmation OTP."""

    status: str = "OTP_SENT"
    email: str
    retry_after: int = Field(default=60, alias="retryAfter")

    model_config = ConfigDict(populate_by_name=True)
