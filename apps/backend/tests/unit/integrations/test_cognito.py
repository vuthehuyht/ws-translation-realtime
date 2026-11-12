"""Unit tests for Cognito Authentication Integration (app.integrations.cognito)."""

import pytest

from app.core.exceptions import (
    ConflictException,
    UnauthorizedException,
    ValidationException,
)
from app.integrations.cognito import get_cognito_client


async def test_cognito_sign_up_and_confirmation_flow() -> None:
    cognito = get_cognito_client()
    email = "host_test@example.com"
    password = "SecurePassword123@"
    name = "Nguyễn Văn Test"

    # 1. Sign Up
    signup_result = await cognito.sign_up(email=email, password=password, full_name=name)
    assert signup_result["userConfirmed"] is False
    assert len(signup_result["userSub"]) > 10

    # 2. Duplicate Sign Up raises Conflict
    with pytest.raises(ConflictException, match="already exists"):
        await cognito.sign_up(email=email, password=password, full_name=name)

    # 3. Authenticate before confirmation fails
    with pytest.raises(UnauthorizedException, match="not confirmed"):
        await cognito.authenticate(email=email, password=password)

    # 4. Confirm with wrong code fails
    with pytest.raises(ValidationException, match="Invalid confirmation code"):
        await cognito.confirm_sign_up(email=email, confirmation_code="000000")

    # 5. Confirm with valid code succeeds
    confirm_result = await cognito.confirm_sign_up(email=email, confirmation_code="123456")
    assert confirm_result["status"] == "CONFIRMED"

    # 6. Authenticate after confirmation succeeds
    auth_result = await cognito.authenticate(email=email, password=password)
    assert "accessToken" in auth_result
    assert auth_result["expiresIn"] == 3600

    # 7. Authenticate with wrong password fails
    with pytest.raises(UnauthorizedException, match="Incorrect username or password"):
        await cognito.authenticate(email=email, password="WrongPassword!")
