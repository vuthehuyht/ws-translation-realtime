"""Unit tests for Cognito Authentication Integration (app.integrations.cognito)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from botocore.exceptions import ClientError

from app.core.config import Settings
from app.core.exceptions import (
    BadGatewayException,
    ConflictException,
    NotFoundException,
    TooManyRequestsException,
    UnauthorizedException,
    ValidationException,
)
from app.integrations import cognito as cognito_module
from app.integrations.cognito import AwsCognitoClient, MockCognitoClient, get_cognito_client


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
    with pytest.raises(ValidationException, match="Invalid or expired confirmation code"):
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
    with pytest.raises(BadGatewayException, match="Authentication provider error"):
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

    count_before = mock_boto.admin_get_user.await_count
    for err_code in (
        "CodeMismatchException",
        "ExpiredCodeException",
        "NotAuthorizedException",
        "UserNotFoundException",
    ):
        mock_boto.confirm_sign_up.side_effect = _make_client_error(err_code, "Sensitive detail")
        with pytest.raises(ValidationException, match="Invalid or expired confirmation code"):
            await cognito.confirm_sign_up("host@example.com", "000000")
    # Never fall back to admin_get_user on confirm failures (prevents unauthenticated bypass).
    assert mock_boto.admin_get_user.await_count == count_before

    mock_boto.initiate_auth.side_effect = _make_client_error(
        "NotAuthorizedException", "Wrong password"
    )
    with pytest.raises(UnauthorizedException, match="Incorrect username or password"):
        await cognito.authenticate("host@example.com", "wrong")

    mock_boto.initiate_auth.side_effect = _make_client_error(
        "UserNotFoundException", "User does not exist"
    )
    with pytest.raises(UnauthorizedException, match="Incorrect username or password"):
        await cognito.authenticate("missing@example.com", "Password123@")

    mock_boto.initiate_auth.side_effect = _make_client_error(
        "UserNotConfirmedException", "User is not confirmed"
    )
    with pytest.raises(UnauthorizedException, match="not confirmed"):
        await cognito.authenticate("unconfirmed@example.com", "Password123@")

    mock_boto.initiate_auth.side_effect = _make_client_error(
        "PasswordResetRequiredException", "Reset required"
    )
    with pytest.raises(UnauthorizedException, match="Password reset required"):
        await cognito.authenticate("reset@example.com", "Password123@")

    mock_boto.initiate_auth.side_effect = _make_client_error(
        "InvalidParameterException", "Invalid auth parameter"
    )
    with pytest.raises(ValidationException, match="Invalid auth parameter"):
        await cognito.authenticate("host@example.com", "")

    mock_boto.initiate_auth.side_effect = _make_client_error(
        "TooManyRequestsException", "Rate exceeded"
    )
    with pytest.raises(TooManyRequestsException, match="Too many login attempts"):
        await cognito.authenticate("host@example.com", "Password123@")

    mock_boto.initiate_auth.side_effect = None
    mock_boto.initiate_auth.return_value = {"ChallengeName": "NEW_PASSWORD_REQUIRED"}
    with pytest.raises(UnauthorizedException, match="NEW_PASSWORD_REQUIRED"):
        await cognito.authenticate("host@example.com", "Password123@")

    mock_boto.initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "acc-aws",
            "IdToken": "id-aws",
        }
    }
    with pytest.raises(UnauthorizedException, match="authentication challenge"):
        await cognito.authenticate("host@example.com", "Password123@")

    mock_boto.initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "acc-aws",
            "IdToken": "id-aws",
            "RefreshToken": "ref-aws",
            "ExpiresIn": 3600,
        }
    }
    ok_auth = await cognito.authenticate("host@example.com", "Password123@")
    assert ok_auth["accessToken"] == "acc-aws"


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


def test_get_cognito_client_selection_by_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cognito_module, "_cognito_instance", None)

    # 1. env="local" with real Cognito IDs -> AwsCognitoClient
    local_live_settings = Settings(
        env="local",
        cognito_user_pool_id="ap-southeast-1_LivePool",
        cognito_client_id="liveclient123",
        aws_access_key_id="AKIATEST",
        aws_secret_access_key="SECRETTEST",
    )
    monkeypatch.setattr(cognito_module, "get_settings", lambda: local_live_settings)
    client = cognito_module.get_cognito_client()
    assert isinstance(client, AwsCognitoClient)

    # 2. env="local" with placeholder _local ID -> MockCognitoClient
    monkeypatch.setattr(cognito_module, "_cognito_instance", None)
    local_mock_settings = Settings(
        env="local",
        cognito_user_pool_id="ap-southeast-1_local",
        cognito_client_id="local_client_id",
    )
    monkeypatch.setattr(cognito_module, "get_settings", lambda: local_mock_settings)
    assert isinstance(cognito_module.get_cognito_client(), MockCognitoClient)

    # 3. env="test" even with real Cognito IDs -> MockCognitoClient
    monkeypatch.setattr(cognito_module, "_cognito_instance", None)
    test_settings = Settings(
        env="test",
        cognito_user_pool_id="ap-southeast-1_LivePool",
        cognito_client_id="liveclient123",
    )
    monkeypatch.setattr(cognito_module, "get_settings", lambda: test_settings)
    assert isinstance(cognito_module.get_cognito_client(), MockCognitoClient)

    # 4. env="production" with placeholder Cognito IDs fails fast instead of using MockCognitoClient
    monkeypatch.setattr(cognito_module, "_cognito_instance", None)
    fake_prod_settings = Settings.model_construct(
        env="production",
        aws_region="ap-southeast-1",
        aws_access_key_id=None,
        aws_secret_access_key=None,
        cognito_user_pool_id="ap-southeast-1_local",
        cognito_client_id="local_client_id",
    )
    monkeypatch.setattr(cognito_module, "get_settings", lambda: fake_prod_settings)
    with pytest.raises(RuntimeError, match="Live Cognito configuration is required"):
        cognito_module.get_cognito_client()


async def test_mock_cognito_refresh_tokens_lifecycle() -> None:
    cognito = get_cognito_client()
    email = "refresh_mock@example.com"
    password = "SecurePassword123@"

    await cognito.sign_up(email=email, password=password, full_name="Refresh User")
    await cognito.confirm_sign_up(email=email, confirmation_code="123456")
    auth_result = await cognito.authenticate(email=email, password=password)

    refreshed = await cognito.refresh_tokens(auth_result["refreshToken"])
    assert refreshed["accessToken"]
    assert refreshed["idToken"]
    assert refreshed["refreshToken"] is None
    assert refreshed["expiresIn"] == 3600

    with pytest.raises(UnauthorizedException, match="Invalid or expired refresh token"):
        await cognito.refresh_tokens("invalid_refresh_token")

    with pytest.raises(UnauthorizedException, match="Invalid or expired refresh token"):
        await cognito.refresh_tokens("mock_refresh_nonexistent-sub")


async def test_aws_cognito_refresh_tokens_success_and_errors() -> None:
    mock_boto = AsyncMock()
    mock_boto.initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "new-access-jwt",
            "IdToken": "new-id-jwt",
            "ExpiresIn": 3600,
        }
    }
    cognito = _make_aws_cognito_with_mock_client(mock_boto)

    res = await cognito.refresh_tokens("rt-abc")
    assert res == {
        "accessToken": "new-access-jwt",
        "idToken": "new-id-jwt",
        "refreshToken": None,
        "expiresIn": 3600,
    }
    mock_boto.initiate_auth.assert_awaited_once_with(
        ClientId="testclientid",
        AuthFlow="REFRESH_TOKEN_AUTH",
        AuthParameters={"REFRESH_TOKEN": "rt-abc"},
    )

    # Rotation case where Cognito issues a new RefreshToken
    mock_boto.initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "rot-access",
            "IdToken": "rot-id",
            "RefreshToken": "rt-rotated",
            "ExpiresIn": 1800,
        }
    }
    rotated = await cognito.refresh_tokens("rt-abc")
    assert rotated["refreshToken"] == "rt-rotated"
    assert rotated["expiresIn"] == 1800

    # Incomplete AuthenticationResult raises UnauthorizedException
    mock_boto.initiate_auth.return_value = {"ChallengeName": "NEW_PASSWORD_REQUIRED"}
    with pytest.raises(UnauthorizedException, match="challenge"):
        await cognito.refresh_tokens("rt-abc")

    # Error mappings
    mock_boto.initiate_auth.side_effect = _make_client_error("NotAuthorizedException", "Revoked")
    with pytest.raises(UnauthorizedException, match="Invalid or expired refresh token"):
        await cognito.refresh_tokens("rt-abc")

    mock_boto.initiate_auth.side_effect = _make_client_error("TooManyRequestsException", "Slow")
    with pytest.raises(TooManyRequestsException, match="Too many"):
        await cognito.refresh_tokens("rt-abc")

    mock_boto.initiate_auth.side_effect = _make_client_error("InternalErrorException", "Down")
    with pytest.raises(BadGatewayException, match="Down"):
        await cognito.refresh_tokens("rt-abc")


async def test_mock_cognito_revoke_token_and_global_sign_out() -> None:
    cognito = get_cognito_client()
    email = "revoke_mock@example.com"
    password = "SecurePassword123@"

    await cognito.sign_up(email=email, password=password, full_name="Revoke User")
    await cognito.confirm_sign_up(email=email, confirmation_code="123456")
    device_a = await cognito.authenticate(email=email, password=password)
    device_b = await cognito.authenticate(email=email, password=password)
    assert device_a["refreshToken"] != device_b["refreshToken"]

    # Revoking one device leaves the other session usable
    await cognito.revoke_token(device_a["refreshToken"])
    with pytest.raises(UnauthorizedException, match="Invalid or expired refresh token"):
        await cognito.refresh_tokens(device_a["refreshToken"])
    assert (await cognito.refresh_tokens(device_b["refreshToken"]))["accessToken"]

    # Revoking an already revoked token is rejected like real Cognito
    with pytest.raises(UnauthorizedException):
        await cognito.revoke_token(device_a["refreshToken"])

    # Global sign-out kills every remaining refresh token of the user
    await cognito.global_sign_out(device_b["accessToken"])
    with pytest.raises(UnauthorizedException, match="Invalid or expired refresh token"):
        await cognito.refresh_tokens(device_b["refreshToken"])

    with pytest.raises(UnauthorizedException, match="invalid or expired"):
        await cognito.global_sign_out("not-a-jwt")


async def test_aws_cognito_revoke_token_and_global_sign_out() -> None:
    mock_boto = AsyncMock()
    cognito = _make_aws_cognito_with_mock_client(mock_boto)

    await cognito.revoke_token("rt-abc")
    mock_boto.revoke_token.assert_awaited_once_with(Token="rt-abc", ClientId="testclientid")

    await cognito.global_sign_out("access-jwt")
    mock_boto.global_sign_out.assert_awaited_once_with(AccessToken="access-jwt")

    mock_boto.revoke_token.side_effect = _make_client_error("NotAuthorizedException", "Revoked")
    with pytest.raises(UnauthorizedException, match="Invalid or expired refresh token"):
        await cognito.revoke_token("rt-abc")

    mock_boto.revoke_token.side_effect = _make_client_error("TooManyRequestsException", "Slow")
    with pytest.raises(TooManyRequestsException, match="Too many"):
        await cognito.revoke_token("rt-abc")

    mock_boto.revoke_token.side_effect = _make_client_error("InternalErrorException", "Down")
    with pytest.raises(BadGatewayException) as revoke_exc:
        await cognito.revoke_token("rt-abc")
    # Provider detail must not leak to clients
    assert "Down" not in revoke_exc.value.message

    # A misconfigured client/token type must not look like a successful revocation
    mock_boto.revoke_token.side_effect = _make_client_error("InvalidParameterException", "bad")
    with pytest.raises(BadGatewayException):
        await cognito.revoke_token("rt-abc")

    mock_boto.global_sign_out.side_effect = _make_client_error("NotAuthorizedException", "Expired")
    with pytest.raises(UnauthorizedException, match="invalid or expired"):
        await cognito.global_sign_out("access-jwt")

    mock_boto.global_sign_out.side_effect = _make_client_error("InternalErrorException", "Down")
    with pytest.raises(BadGatewayException) as global_exc:
        await cognito.global_sign_out("access-jwt")
    assert "Down" not in global_exc.value.message


async def test_mock_cognito_forgot_password_confirmed_user() -> None:
    cognito = MockCognitoClient()
    email = "host@example.com"
    await cognito.sign_up(email=email, password="Password123@", full_name="Host")
    await cognito.confirm_sign_up(email=email, confirmation_code="123456")

    result = await cognito.forgot_password(email)

    assert result["codeDeliveryDetails"]["Destination"] == email
    assert result["codeDeliveryDetails"]["DeliveryMedium"] == "EMAIL"
    assert cognito.users[email].reset_code == "123456"


async def test_mock_cognito_forgot_password_unknown_user_raises_not_found() -> None:
    cognito = MockCognitoClient()

    with pytest.raises(NotFoundException, match="User not found"):
        await cognito.forgot_password("missing@example.com")


async def test_mock_cognito_forgot_password_unconfirmed_user_raises_conflict() -> None:
    cognito = MockCognitoClient()
    email = "unconfirmed@example.com"
    await cognito.sign_up(email=email, password="Password123@", full_name="Unconfirmed")

    with pytest.raises(ConflictException, match="not eligible"):
        await cognito.forgot_password(email)


async def test_aws_cognito_forgot_password_success() -> None:
    mock_boto = AsyncMock()
    mock_boto.forgot_password.return_value = {
        "CodeDeliveryDetails": {"Destination": "h***@example.com", "DeliveryMedium": "EMAIL"}
    }
    cognito = _make_aws_cognito_with_mock_client(mock_boto)

    result = await cognito.forgot_password("host@example.com")

    mock_boto.forgot_password.assert_awaited_once_with(
        ClientId="testclientid",
        Username="host@example.com",
    )
    assert result["codeDeliveryDetails"]["DeliveryMedium"] == "EMAIL"


@pytest.mark.parametrize(
    ("error_code", "expected_exc"),
    [
        ("UserNotFoundException", NotFoundException),
        ("InvalidParameterException", ConflictException),
        ("NotAuthorizedException", ConflictException),
        ("UserNotConfirmedException", ConflictException),
        ("LimitExceededException", TooManyRequestsException),
        ("TooManyRequestsException", TooManyRequestsException),
        ("CodeDeliveryFailureException", BadGatewayException),
        ("InternalErrorException", BadGatewayException),
    ],
)
async def test_aws_cognito_forgot_password_maps_client_errors(
    error_code: str,
    expected_exc: type[Exception],
) -> None:
    mock_boto = AsyncMock()
    mock_boto.forgot_password.side_effect = _make_client_error(error_code, "sensitive detail")
    cognito = _make_aws_cognito_with_mock_client(mock_boto)

    with pytest.raises(expected_exc) as exc_info:
        await cognito.forgot_password("host@example.com")

    assert "sensitive detail" not in str(exc_info.value)


@pytest.mark.parametrize(
    ("error_code", "expected_exc"),
    [
        ("CodeMismatchException", ValidationException),
        ("ExpiredCodeException", ValidationException),
        ("UserNotFoundException", ValidationException),
        ("NotAuthorizedException", ValidationException),
        ("InvalidPasswordException", ValidationException),
        ("LimitExceededException", TooManyRequestsException),
        ("TooManyRequestsException", TooManyRequestsException),
        ("InternalErrorException", BadGatewayException),
    ],
)
async def test_aws_cognito_confirm_forgot_password_maps_client_errors(
    error_code: str,
    expected_exc: type[Exception],
) -> None:
    mock_boto = AsyncMock()
    mock_boto.confirm_forgot_password.side_effect = _make_client_error(
        error_code, "Cognito reset detail"
    )
    cognito = _make_aws_cognito_with_mock_client(mock_boto)

    with pytest.raises(expected_exc):
        await cognito.confirm_forgot_password("host@example.com", "123456", "NewPassword2@")


async def test_aws_cognito_admin_global_sign_out_calls_api_and_ignores_missing_user() -> None:
    mock_boto = AsyncMock()
    cognito = _make_aws_cognito_with_mock_client(mock_boto)

    await cognito.admin_global_sign_out("host@example.com")
    mock_boto.admin_user_global_sign_out.assert_awaited_once_with(
        UserPoolId="ap-southeast-1_testpool",
        Username="host@example.com",
    )

    mock_boto.admin_user_global_sign_out.side_effect = _make_client_error(
        "UserNotFoundException", "User does not exist"
    )
    await cognito.admin_global_sign_out("missing@example.com")


@pytest.mark.parametrize("error_code", ["InvalidPasswordException", "InvalidParameterException"])
async def test_aws_cognito_confirm_forgot_password_hides_raw_provider_message(
    error_code: str,
) -> None:
    mock_boto = AsyncMock()
    mock_boto.confirm_forgot_password.side_effect = _make_client_error(
        error_code, "raw provider detail"
    )
    cognito = _make_aws_cognito_with_mock_client(mock_boto)

    with pytest.raises(ValidationException) as exc_info:
        await cognito.confirm_forgot_password("host@example.com", "123456", "NewPassword2@")

    assert "raw provider detail" not in str(exc_info.value)


async def test_aws_cognito_admin_global_sign_out_raises_bad_gateway_on_access_denied() -> None:
    mock_boto = AsyncMock()
    mock_boto.admin_user_global_sign_out.side_effect = _make_client_error(
        "AccessDeniedException", "not authorized to perform"
    )
    cognito = _make_aws_cognito_with_mock_client(mock_boto)

    with pytest.raises(BadGatewayException):
        await cognito.admin_global_sign_out("host@example.com")


async def test_mock_cognito_delete_user_removes_account_and_sessions() -> None:
    cognito = MockCognitoClient()
    email = "delete.mock@example.com"
    password = "SecurePassword123@"

    await cognito.sign_up(email=email, password=password, full_name="Delete Mock")
    await cognito.confirm_sign_up(email=email, confirmation_code="123456")
    tokens = await cognito.authenticate(email=email, password=password)

    await cognito.delete_user(tokens["accessToken"])

    assert email not in cognito.users
    with pytest.raises(UnauthorizedException):
        await cognito.refresh_tokens(tokens["refreshToken"])
    with pytest.raises(UnauthorizedException):
        await cognito.delete_user(tokens["accessToken"])


async def test_aws_cognito_delete_user_success_and_error_mappings() -> None:
    mock_boto = AsyncMock()
    cognito = _make_aws_cognito_with_mock_client(mock_boto)

    await cognito.delete_user("access-jwt")
    mock_boto.delete_user.assert_awaited_once_with(AccessToken="access-jwt")

    mock_boto.delete_user.side_effect = _make_client_error("NotAuthorizedException", "Expired")
    with pytest.raises(UnauthorizedException, match="invalid or expired"):
        await cognito.delete_user("access-jwt")

    mock_boto.delete_user.side_effect = _make_client_error("TooManyRequestsException", "Rate")
    with pytest.raises(TooManyRequestsException, match="Too many"):
        await cognito.delete_user("access-jwt")

    mock_boto.delete_user.side_effect = _make_client_error("InternalErrorException", "Down")
    with pytest.raises(BadGatewayException):
        await cognito.delete_user("access-jwt")
