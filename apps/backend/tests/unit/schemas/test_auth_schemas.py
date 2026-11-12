"""Unit tests for Auth Request and Response Schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.requests import ConfirmRequest, LoginRequest, RegisterRequest
from app.schemas.responses import (
    LoginResponse,
    RegisterResponse,
    TokenResponse,
    UserProfileResponse,
)


def test_register_request_validation() -> None:
    # Valid payload
    req = RegisterRequest(
        email="user@example.com",
        password="SuperPassword123@",
        full_name="Valid User",
        role="HOST",
    )
    assert req.email == "user@example.com"
    assert req.role == "HOST"

    # Invalid email
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="invalid-email",
            password="SuperPassword123@",
            full_name="Valid User",
        )

    # Password too short (< 8 chars)
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="user@example.com",
            password="123",
            full_name="Valid User",
        )

    # Invalid role
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="user@example.com",
            password="SuperPassword123@",
            full_name="Valid User",
            role="SUPERUSER",
        )


def test_confirm_request_validation() -> None:
    # Valid OTP (6 digits)
    req = ConfirmRequest(email="user@example.com", confirmation_code="123456")
    assert req.confirmation_code == "123456"

    # Non-digit code
    with pytest.raises(ValidationError):
        ConfirmRequest(email="user@example.com", confirmation_code="abcdef")

    # Code length not equal to 6
    with pytest.raises(ValidationError):
        ConfirmRequest(email="user@example.com", confirmation_code="12345")


def test_login_request_and_response_serialization() -> None:
    login_req = LoginRequest(email="user@example.com", password="Password123@")
    assert login_req.email == "user@example.com"

    tokens = TokenResponse(
        accessToken="access_token_123",
        idToken="id_token_123",
        refreshToken="refresh_token_123",
        expiresIn=3600,
    )
    user_profile = UserProfileResponse(
        id="sub-123",
        email="user@example.com",
        role="HOST",
        status="ACTIVE",
        fullName="Host User",
    )
    login_res = LoginResponse(tokens=tokens, user=user_profile)

    res_dict = login_res.model_dump(by_alias=True)
    assert res_dict["tokens"]["accessToken"] == "access_token_123"
    assert res_dict["user"]["fullName"] == "Host User"


def test_register_response_alias() -> None:
    resp = RegisterResponse(userId="sub-456", email="test@example.com")
    res_dict = resp.model_dump(by_alias=True)
    assert res_dict["userId"] == "sub-456"
    assert res_dict["status"] == "PENDING_CONFIRMATION"
