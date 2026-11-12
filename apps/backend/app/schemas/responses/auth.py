"""Authentication Response Schemas."""

from pydantic import BaseModel, ConfigDict, Field


class RegisterResponse(BaseModel):
    """Response returned upon successful registration."""

    user_id: str = Field(..., alias="userId")
    email: str
    status: str = "PENDING_CONFIRMATION"

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
