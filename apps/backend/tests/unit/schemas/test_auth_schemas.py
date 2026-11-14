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


def test_register_request_password_complexity() -> None:
    # 1. Valid password (8+ chars, uppercase, lowercase, digit, special char)
    valid_req = RegisterRequest(
        email="host@example.com",
        password="ValidPassword123@",
        fullName="Nguyen Van Host",
    )
    assert valid_req.password == "ValidPassword123@"
    assert valid_req.full_name == "Nguyen Van Host"

    # 2. Support snake_case full_name
    valid_snake = RegisterRequest(
        email="host@example.com",
        password="ValidPassword123@",
        full_name="Nguyen Van Host",
    )
    assert valid_snake.full_name == "Nguyen Van Host"

    # 3. Too short (< 8 chars)
    with pytest.raises(ValidationError, match="at least 8 characters"):
        RegisterRequest(
            email="host@example.com",
            password="Val1@",
            fullName="Nguyen Van Host",
        )

    # 4. Missing uppercase
    with pytest.raises(ValidationError, match="uppercase"):
        RegisterRequest(
            email="host@example.com",
            password="validpassword123@",
            fullName="Nguyen Van Host",
        )

    # 5. Missing lowercase
    with pytest.raises(ValidationError, match="lowercase"):
        RegisterRequest(
            email="host@example.com",
            password="VALIDPASSWORD123@",
            fullName="Nguyen Van Host",
        )

    # 6. Missing number
    with pytest.raises(ValidationError, match="number"):
        RegisterRequest(
            email="host@example.com",
            password="ValidPassword!@#",
            fullName="Nguyen Van Host",
        )

    # 7. Missing special character
    with pytest.raises(ValidationError, match="special character"):
        RegisterRequest(
            email="host@example.com",
            password="ValidPassword1234",
            fullName="Nguyen Van Host",
        )

    # 8. Invalid email
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="invalid-email-format",
            password="ValidPassword123@",
            fullName="Nguyen Van Host",
        )

    # 9. Admin role is not allowed on public registration
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="host@example.com",
            password="ValidPassword123@",
            fullName="Nguyen Van Host",
            role="ADMIN",
        )

    # 10. Email is trimmed and lowercased before validation
    trimmed_req = RegisterRequest(
        email="  Host.User@Example.COM ",
        password="ValidPassword123@",
        fullName="Nguyen Van Host",
    )
    assert trimmed_req.email == "host.user@example.com"


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


def test_register_response_serialization_and_aliases() -> None:
    # 1. By userSub alias
    resp1 = RegisterResponse(userSub="sub-uuid-123", email="test@example.com")
    assert resp1.user_sub == "sub-uuid-123"
    assert resp1.user_id == "sub-uuid-123"
    assert resp1.status == "CONFIRMATION_REQUIRED"

    dumped = resp1.model_dump(by_alias=True)
    assert dumped["userSub"] == "sub-uuid-123"
    assert dumped["status"] == "CONFIRMATION_REQUIRED"
    assert dumped["email"] == "test@example.com"

    # 2. By userId alias for backward compatibility
    resp2 = RegisterResponse(userId="sub-uuid-456", email="test2@example.com")
    assert resp2.user_sub == "sub-uuid-456"
    assert resp2.user_id == "sub-uuid-456"
