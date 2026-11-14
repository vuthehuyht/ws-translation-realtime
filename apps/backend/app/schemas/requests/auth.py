"""Authentication Request Schemas."""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Standard RFC 5322 compatible email pattern
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class _EmailRequestBase(BaseModel):
    """Shared base model normalizing email before regex validation."""

    @field_validator("email", mode="before", check_fields=False)
    @classmethod
    def normalize_email(cls, v: object) -> object:
        """Trim whitespace and lowercase email strings prior to pattern validation."""
        if isinstance(v, str):
            return v.strip().lower()
        return v


class RegisterRequest(_EmailRequestBase):
    """Payload for host or user registration."""

    email: str = Field(..., pattern=EMAIL_REGEX, description="Valid email address")
    password: str = Field(..., min_length=8, description="Password min 8 characters")
    full_name: str = Field(..., min_length=2, max_length=100, alias="fullName")
    role: str = Field(default="HOST", pattern="^(HOST|LISTENER)$")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Validate password minimum complexity: uppercase, lowercase, digit, special char."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>\-_+=~`[\]\\;/]', v):
            raise ValueError("Password must contain at least one special character")
        return v


class ConfirmRequest(_EmailRequestBase):
    """Payload to confirm registration with OTP code."""

    email: str = Field(..., pattern=EMAIL_REGEX)
    confirmation_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class LoginRequest(_EmailRequestBase):
    """Payload for user authentication."""

    email: str = Field(..., pattern=EMAIL_REGEX)
    password: str
