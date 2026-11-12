"""Authentication Request Schemas."""

from pydantic import BaseModel, Field

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class RegisterRequest(BaseModel):
    """Payload for host or user registration."""

    email: str = Field(..., pattern=EMAIL_REGEX, description="Valid email address")
    password: str = Field(..., min_length=8, description="Password min 8 characters")
    full_name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(default="HOST", pattern="^(HOST|LISTENER|ADMIN)$")


class ConfirmRequest(BaseModel):
    """Payload to confirm registration with OTP code."""

    email: str = Field(..., pattern=EMAIL_REGEX)
    confirmation_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class LoginRequest(BaseModel):
    """Payload for user authentication."""

    email: str = Field(..., pattern=EMAIL_REGEX)
    password: str
