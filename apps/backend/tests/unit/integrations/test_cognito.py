"""Unit tests for Cognito Authentication Integration (app.integrations.cognito)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from botocore.exceptions import ClientError

from app.core.exceptions import (
    BadGatewayException,
    ConflictException,
    NotFoundException,
    TooManyRequestsException,
    UnauthorizedException,
    ValidationException,
)
from app.integrations.cognito import AwsCognitoClient, get_cognito_client


def _make_client_error(code: str, message: str = "error") -> ClientError:
    """Build a botocore ClientError for testing Cognito error mapping."""
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "CognitoOperation",
    )


def _make_aws_cognito_with_mock_client(mock_boto_client: AsyncMock) -> AwsCognitoClient:
    """Create AwsCognitoClient with mocked aioboto3 Session.client context manager."""
    cognito = AwsCognitoClient(
        user_pool_id="ap-southeast-1_testpool",
        client_id="testclientid",
        region="ap-southeast-1",
    )
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_boto_client)
    ctx.__aexit__ = AsyncMock(return_value=False)
    cognito.session = MagicMock()
    cognito.session.client.return_value = ctx
    return cognito


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


async def test_aws_cognito_sign_up_success_and_error_mappings() -> None:
    mock_boto = AsyncMock()
    mock_boto.sign_up.return_value = {
        "UserSub": "sub-aws-123",
        "UserConfirmed": False,
        "CodeDeliveryDetails": {"DeliveryMedium": "EMAIL"},
    }
    cognito = _make_aws_cognito_with_mock_client(mock_boto)

    res = await cognito.sign_up(
        email="host@example.com",
        password="ValidPassword123@",
        full_name="Host User",
    )
    assert res["userSub"] == "sub-aws-123"
    assert res["status"] == "CONFIRMATION_REQUIRED"
    mock_boto.sign_up.assert_awaited_once_with(
        ClientId="testclientid",
        Username="host@example.com",
        Password="ValidPassword123@",
        UserAttributes=[
            {"Name": "email", "Value": "host@example.com"},
            {"Name": "name", "Value": "Host User"},
        ],
    )

    mock_boto.sign_up.side_effect = _make_client_error("UsernameExistsException", "Exists")
    with pytest.raises(ConflictException, match="already exists"):
        await cognito.sign_up("host@example.com", "ValidPassword123@", "Host User")

    mock_boto.sign_up.side_effect = _make_client_error("InvalidPasswordException", "Weak")
    with pytest.raises(ValidationException, match="Weak"):
        await cognito.sign_up("host@example.com", "weak", "Host User")

    mock_boto.sign_up.side_effect = _make_client_error("InternalErrorException", "Boom")
    with pytest.raises(BadGatewayException, match="Boom"):
        await cognito.sign_up("host@example.com", "ValidPassword123@", "Host User")


async def test_aws_cognito_get_user_info_and_confirm_errors() -> None:
    mock_boto = AsyncMock()
    mock_boto.admin_get_user.return_value = {
        "UserAttributes": [
            {"Name": "sub", "Value": "sub-aws-456"},
            {"Name": "name", "Value": "Nguyễn Văn A"},
        ]
    }
    cognito = _make_aws_cognito_with_mock_client(mock_boto)

    info = await cognito.get_user_info("host@example.com")
    assert info == {"sub": "sub-aws-456", "name": "Nguyễn Văn A"}
    assert await cognito.get_user_sub("host@example.com") == "sub-aws-456"

    mock_boto.admin_get_user.side_effect = _make_client_error("UserNotFoundException", "Missing")
    with pytest.raises(NotFoundException, match="not found"):
        await cognito.get_user_info("missing@example.com")

    mock_boto.confirm_sign_up.side_effect = _make_client_error(
        "CodeMismatchException", "Bad code"
    )
    mock_boto.admin_get_user.side_effect = None
    mock_boto.admin_get_user.return_value = {"UserStatus": "UNCONFIRMED", "UserAttributes": []}
    with pytest.raises(ValidationException, match="Bad code"):
        await cognito.confirm_sign_up("host@example.com", "000000")

    # Idempotent confirm when Cognito user is already CONFIRMED (CodeMismatchException)
    mock_boto.confirm_sign_up.side_effect = _make_client_error(
        "CodeMismatchException", "Invalid code provided, please request a code again."
    )
    mock_boto.admin_get_user.return_value = {
        "UserStatus": "CONFIRMED",
        "UserAttributes": [
            {"Name": "sub", "Value": "sub-aws-456"},
            {"Name": "name", "Value": "Nguyễn Văn A"},
        ],
    }
    idempotent_res = await cognito.confirm_sign_up("host@example.com", "123456")
    assert idempotent_res == {
        "status": "CONFIRMED",
        "sub": "sub-aws-456",
        "name": "Nguyễn Văn A",
    }

    # Idempotent confirm when Cognito raises NotAuthorizedException for CONFIRMED user
    mock_boto.confirm_sign_up.side_effect = _make_client_error(
        "NotAuthorizedException", "User cannot be confirmed. Current status is CONFIRMED"
    )
    idempotent_not_auth = await cognito.confirm_sign_up("host@example.com", "123456")
    assert idempotent_not_auth["status"] == "CONFIRMED"

    # NotAuthorizedException when user is still UNCONFIRMED raises UnauthorizedException
    mock_boto.admin_get_user.return_value = {"UserStatus": "UNCONFIRMED", "UserAttributes": []}
    with pytest.raises(UnauthorizedException, match="cannot be confirmed"):
        await cognito.confirm_sign_up("host@example.com", "123456")

    mock_boto.initiate_auth.side_effect = _make_client_error(
        "NotAuthorizedException", "Wrong password"
    )
    with pytest.raises(UnauthorizedException, match="Incorrect username or password"):
        await cognito.authenticate("host@example.com", "wrong")


async def test_aws_cognito_resend_confirmation_code() -> None:
    mock_boto = AsyncMock()
    mock_boto.resend_confirmation_code.return_value = {
        "CodeDeliveryDetails": {"DeliveryMedium": "EMAIL", "Destination": "host@example.com"}
    }
    cognito = _make_aws_cognito_with_mock_client(mock_boto)

    res = await cognito.resend_confirmation_code("host@example.com")
    assert res["codeDeliveryDetails"]["DeliveryMedium"] == "EMAIL"

    mock_boto.resend_confirmation_code.side_effect = _make_client_error(
        "InvalidParameterException", "User is already confirmed"
    )
    with pytest.raises(ConflictException, match="already confirmed"):
        await cognito.resend_confirmation_code("host@example.com")

    mock_boto.resend_confirmation_code.side_effect = _make_client_error(
        "LimitExceededException", "Attempt limit exceeded"
    )
    with pytest.raises(TooManyRequestsException, match="Too many OTP requests"):
        await cognito.resend_confirmation_code("host@example.com")

    mock_boto.resend_confirmation_code.side_effect = _make_client_error(
        "UserNotFoundException", "User does not exist"
    )
    with pytest.raises(NotFoundException, match="not found"):
        await cognito.resend_confirmation_code("missing@example.com")
