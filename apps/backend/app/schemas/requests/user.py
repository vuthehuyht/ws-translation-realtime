"""User Profile, Preferences, Billing Info, Avatar, and Security Request Schemas."""

import re
import zoneinfo
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.requests.auth import _validate_password_complexity

# E.164 international phone number format: + followed by 7 to 15 digits.
E164_PHONE_REGEX = re.compile(r"^\+[1-9]\d{6,14}$")

# Vietnamese / standard 10-digit or 13-digit tax code (optionally formatted as 10-3).
TAX_CODE_REGEX = re.compile(r"^(?:\d{10}|\d{13}|\d{10}-\d{3})$")

# Supported AWS Transcribe Streaming source languages & Translate target languages.
SUPPORTED_LANGUAGES: frozenset[str] = frozenset(
    {
        "vi-VN",
        "en-US",
        "en-GB",
        "en-AU",
        "ja-JP",
        "ko-KR",
        "zh-CN",
        "zh-TW",
        "fr-FR",
        "de-DE",
        "es-ES",
        "es-US",
        "it-IT",
        "pt-BR",
        "th-TH",
        "id-ID",
        "ms-MY",
        "ru-RU",
        "ar-SA",
        "hi-IN",
    }
)

# Fallback IANA timezone pattern used on platforms without system tzdata (e.g., Windows).
IANA_TIMEZONE_PATTERN = re.compile(
    r"^(?:UTC|Etc/UTC|Etc/GMT(?:[+-](?:1[0-4]|[0-9]))?|"
    r"(?:Africa|America|Antarctica|Arctic|Asia|Atlantic|Australia|Europe|Indian|Pacific)"
    r"/[A-Za-z0-9_+\-]+(?:/[A-Za-z0-9_+\-]+)?)$"
)

MAX_AVATAR_SIZE_BYTES = 2_097_152  # 2 MB
ALLOWED_AVATAR_MIME_TYPES = Literal["image/jpeg", "image/png", "image/webp"]
ALLOWED_PREFERENCE_KEYS: frozenset[str] = frozenset(
    {"vadSensitivity", "subtitleMode", "uiLanguage"}
)


def _is_valid_timezone(tz: str) -> bool:
    """Validate against system IANA tzdb when available, otherwise standard IANA region syntax."""
    available = zoneinfo.available_timezones()
    if available:
        return tz in available
    return bool(IANA_TIMEZONE_PATTERN.match(tz))


class UpdateProfileRequest(BaseModel):
    """Payload for updating basic user profile metadata (PATCH /users/me/profile)."""

    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        validation_alias=AliasChoices("fullName", "full_name"),
    )
    phone_number: str | None = Field(
        default=None,
        max_length=32,
        validation_alias=AliasChoices("phoneNumber", "phone_number"),
    )
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    bio: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone_number(cls, v: object) -> object:
        if isinstance(v, str):
            cleaned = re.sub(r"[\s\-().]", "", v.strip())
            return cleaned or None
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str | None) -> str | None:
        if v is not None and not E164_PHONE_REGEX.match(v):
            raise ValueError("Phone number must be in E.164 format (e.g. +84901234567)")
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str | None) -> str | None:
        if v is not None:
            tz = v.strip()
            if not _is_valid_timezone(tz):
                raise ValueError(f"Unsupported IANA timezone: {tz}")
            return tz
        return v

    @field_validator("bio", mode="before")
    @classmethod
    def normalize_bio(cls, v: object) -> object:
        if isinstance(v, str):
            stripped = v.strip()
            return stripped or None
        return v


class UpdatePreferencesRequest(BaseModel):
    """Payload for updating default translation languages & UI preferences."""

    default_source_lang: str | None = Field(
        default=None,
        validation_alias=AliasChoices("defaultSourceLang", "default_source_lang"),
    )
    default_target_langs: list[str] | None = Field(
        default=None,
        min_length=1,
        max_length=10,
        validation_alias=AliasChoices("defaultTargetLangs", "default_target_langs"),
    )
    preferences: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("default_source_lang")
    @classmethod
    def validate_source_lang(cls, v: str | None) -> str | None:
        if v is not None and v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported source language: {v}")
        return v

    @field_validator("default_target_langs")
    @classmethod
    def validate_target_langs(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        deduped = list(dict.fromkeys(v))
        if not deduped:
            raise ValueError("At least one target language is required")
        if len(deduped) > 10:
            raise ValueError("Maximum 10 target languages are allowed")
        unsupported = [lang for lang in deduped if lang not in SUPPORTED_LANGUAGES]
        if unsupported:
            raise ValueError(f"Unsupported target languages: {', '.join(unsupported)}")
        return deduped

    @field_validator("preferences")
    @classmethod
    def validate_preferences(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is None:
            return None
        unknown_keys = set(v.keys()) - ALLOWED_PREFERENCE_KEYS
        if unknown_keys:
            raise ValueError(f"Unsupported preference keys: {', '.join(sorted(unknown_keys))}")
        if "vadSensitivity" in v and v["vadSensitivity"] not in ("low", "medium", "high"):
            raise ValueError("vadSensitivity must be one of: low, medium, high")
        if "subtitleMode" in v and v["subtitleMode"] not in ("bilingual", "target_only"):
            raise ValueError("subtitleMode must be one of: bilingual, target_only")
        if "uiLanguage" in v and v["uiLanguage"] not in ("vi", "en"):
            raise ValueError("uiLanguage must be one of: vi, en")
        return v


class UpdateBillingInfoRequest(BaseModel):
    """Payload for updating VAT / company billing information (PUT /users/me/billing-info)."""

    company_name: str | None = Field(
        default=None,
        max_length=255,
        validation_alias=AliasChoices("companyName", "company_name"),
    )
    tax_code: str | None = Field(
        default=None,
        max_length=64,
        validation_alias=AliasChoices("taxCode", "tax_code"),
    )
    company_address: str | None = Field(
        default=None,
        max_length=512,
        validation_alias=AliasChoices("companyAddress", "company_address"),
    )

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("company_name", "tax_code", "company_address", mode="before")
    @classmethod
    def normalize_optional_text(cls, v: object) -> object:
        if isinstance(v, str):
            stripped = v.strip()
            return stripped or None
        return v

    @field_validator("tax_code")
    @classmethod
    def validate_tax_code(cls, v: str | None) -> str | None:
        if v is not None and not TAX_CODE_REGEX.match(v):
            raise ValueError(
                "Tax code must contain 10 or 13 digits (e.g. 0101234567 or 0101234567-001)"
            )
        return v


class AvatarUploadUrlRequest(BaseModel):
    """Payload to request a presigned S3 upload URL for a user avatar."""

    file_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices("fileName", "file_name"),
    )
    file_type: ALLOWED_AVATAR_MIME_TYPES = Field(
        ...,
        validation_alias=AliasChoices("fileType", "file_type"),
    )
    file_size_bytes: int = Field(
        ...,
        gt=0,
        le=MAX_AVATAR_SIZE_BYTES,
        validation_alias=AliasChoices("fileSizeBytes", "file_size_bytes"),
    )

    model_config = ConfigDict(populate_by_name=True)


class AvatarConfirmRequest(BaseModel):
    """Payload to confirm an uploaded S3 avatar object and persist its CDN URL."""

    s3_key: str = Field(
        ...,
        min_length=1,
        max_length=512,
        validation_alias=AliasChoices("s3Key", "s3_key"),
    )

    model_config = ConfigDict(populate_by_name=True)


class ChangePasswordRequest(BaseModel):
    """Payload to change the authenticated user's password via Cognito."""

    old_password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        validation_alias=AliasChoices("oldPassword", "old_password"),
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        validation_alias=AliasChoices("newPassword", "new_password"),
    )

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_complexity(cls, v: str) -> str:
        """Enforce the same password complexity policy as registration."""
        return _validate_password_complexity(v)

    @model_validator(mode="after")
    def validate_passwords_differ(self) -> "ChangePasswordRequest":
        if self.old_password == self.new_password:
            raise ValueError("New password must be different from current password")
        return self
