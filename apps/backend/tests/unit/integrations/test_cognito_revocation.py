"""Unit tests for Cognito token revocation (RevokeToken and GlobalSignOut)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from botocore.exceptions import ClientError

from app.core.exceptions import (
    BadGatewayException,
    TooManyRequestsException,
    UnauthorizedException,
)
from app.integrations.cognito import AwsCognitoClient, get_cognito_client


def _make_client_error(code: str, message: str = "error") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": message}}, "CognitoOperation")


def _make_aws_cognito_with_mock_client(mock_boto_client: AsyncMock) -> AwsCognitoClient:
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
