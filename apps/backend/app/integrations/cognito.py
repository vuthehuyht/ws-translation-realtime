"""Cognito Integration: Amazon Cognito User Pool Host Authentication.

Wraps SignUp, ConfirmSignUp, ResendConfirmationCode, InitiateAuth, and AdminGetUser
with automatic offline mock support for local and test environments.
"""

import logging
import os
import uuid
from dataclasses import dataclass
from typing import Any

import aioboto3
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.core.exceptions import (
    BadGatewayException,
    ConflictException,
    NotFoundException,
    TooManyRequestsException,
    UnauthorizedException,
    ValidationException,
)
from app.core.security import create_access_token, decode_access_token
from app.integrations.cognito_jwks import CognitoJwtVerifier

logger = logging.getLogger(__name__)


@dataclass
class CognitoUserRecord:
    """Internal user record held by the offline Cognito mock."""

    sub: str
    email: str
    password: str
    full_name: str
    is_confirmed: bool = False
    confirmation_code: str = "123456"


@dataclass(frozen=True)
class MockRefreshSession:
    """Owner and session id (`origin_jti`) behind a mock refresh token."""

    sub: str
    origin_jti: str


class CognitoClient:
    """Interface for Amazon Cognito Identity Provider operations."""

    async def sign_up(self, email: str, password: str, full_name: str) -> dict[str, Any]:
        """Register a new user in Cognito."""
        raise NotImplementedError

    async def confirm_sign_up(self, email: str, confirmation_code: str) -> dict[str, Any]:
        """Confirm user registration with verification code."""
        raise NotImplementedError

    async def resend_confirmation_code(self, email: str) -> dict[str, Any]:
        """Resend OTP code."""
        raise NotImplementedError

    async def authenticate(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate user credentials."""
        raise NotImplementedError

    async def refresh_tokens(self, refresh_token: str) -> dict[str, Any]:
        """Refresh AccessToken and IdToken using Cognito REFRESH_TOKEN_AUTH."""
        raise NotImplementedError

    async def revoke_token(self, refresh_token: str) -> None:
        """Revoke a single refresh token (and the access tokens issued from it)."""
        raise NotImplementedError

    async def global_sign_out(self, access_token: str) -> None:
        """Invalidate every refresh token of the access token's user on all devices."""
        raise NotImplementedError

    async def verify_access_token(self, token: str, *, verify_exp: bool = True) -> dict[str, Any]:
        """Verify an access token and return its claims; raise ValueError when invalid."""
        raise NotImplementedError

    async def get_user_info(self, email: str) -> dict[str, str]:
        """Fetch user attributes (sub, name) from Cognito."""
        raise NotImplementedError

    async def get_user_sub(self, email: str) -> str:
        """Fetch user sub UUID."""
        info = await self.get_user_info(email)
        return info["sub"]


class MockCognitoClient(CognitoClient):
    """In-memory offline mock for local development and pytest suites."""

    def __init__(self) -> None:
        self.users: dict[str, CognitoUserRecord] = {}
        # Active refresh tokens and their sessions so revocation can be simulated.
        self.refresh_sessions: dict[str, MockRefreshSession] = {}

    async def sign_up(self, email: str, password: str, full_name: str) -> dict[str, Any]:
        if email in self.users:
            raise ConflictException("User account already exists")
        user_sub = str(uuid.uuid4())
        self.users[email] = CognitoUserRecord(
            sub=user_sub,
            email=email,
            password=password,
            full_name=full_name,
            is_confirmed=False,
            confirmation_code="123456",
        )
        logger.info("Mock Cognito sign_up completed (sub=%s)", user_sub)
        return {
            "userSub": user_sub,
            "userConfirmed": False,
            "status": "CONFIRMATION_REQUIRED",
            "codeDeliveryDetails": {"Destination": email, "DeliveryMedium": "EMAIL"},
        }

    async def confirm_sign_up(self, email: str, confirmation_code: str) -> dict[str, Any]:
        user = self.users.get(email)
        if not user or confirmation_code != user.confirmation_code:
            raise ValidationException("Invalid or expired confirmation code")
        user.is_confirmed = True
        logger.info("Mock Cognito confirmed sign_up (sub=%s)", user.sub)
        return {"status": "CONFIRMED", "sub": user.sub}

    async def resend_confirmation_code(self, email: str) -> dict[str, Any]:
        user = self.users.get(email)
        if not user:
            raise NotFoundException("User not found")
        if user.is_confirmed:
            raise ConflictException("User is already confirmed")
        logger.info("Mock Cognito resend_confirmation_code (sub=%s)", user.sub)
        return {"codeDeliveryDetails": {"Destination": email, "DeliveryMedium": "EMAIL"}}

    async def authenticate(self, email: str, password: str) -> dict[str, Any]:
        user = self.users.get(email)
        if not user or user.password != password:
            raise UnauthorizedException("Incorrect username or password")
        if not user.is_confirmed:
            raise UnauthorizedException("User is not confirmed. Please enter OTP")

        refresh_token = f"mock_refresh_{uuid.uuid4().hex}"
        session = MockRefreshSession(sub=user.sub, origin_jti=uuid.uuid4().hex)
        self.refresh_sessions[refresh_token] = session
        access_token, id_token = self._issue_tokens(user, session)
        return {
            "accessToken": access_token,
            "idToken": id_token,
            "refreshToken": refresh_token,
            "expiresIn": 3600,
        }

    @staticmethod
    def _issue_tokens(user: CognitoUserRecord, session: MockRefreshSession) -> tuple[str, str]:
        """Issue access/ID tokens that, like real Cognito, carry a unique jti and origin_jti."""
        common = {
            "email": user.email,
            "name": user.full_name,
            "origin_jti": session.origin_jti,
        }
        access_token = create_access_token(
            subject=user.sub, claims={**common, "jti": uuid.uuid4().hex}
        )
        id_token = create_access_token(
            subject=user.sub,
            claims={**common, "jti": uuid.uuid4().hex, "token_use": "id"},
        )
        return access_token, id_token

    async def refresh_tokens(self, refresh_token: str) -> dict[str, Any]:
        session = self.refresh_sessions.get(refresh_token)
        if session is None:
            raise UnauthorizedException("Invalid or expired refresh token")

        user = next((u for u in self.users.values() if u.sub == session.sub), None)
        if not user or not user.is_confirmed:
            raise UnauthorizedException("Invalid or expired refresh token")

        access_token, id_token = self._issue_tokens(user, session)
        return {
            "accessToken": access_token,
            "idToken": id_token,
            "refreshToken": None,
            "expiresIn": 3600,
        }

    async def revoke_token(self, refresh_token: str) -> None:
        # Real Cognito rejects unknown or already revoked tokens; mirror that.
        if self.refresh_sessions.pop(refresh_token, None) is None:
            raise UnauthorizedException("Invalid or expired refresh token")

    async def global_sign_out(self, access_token: str) -> None:
        try:
            subject = decode_access_token(access_token).get("sub")
        except ValueError as e:
            raise UnauthorizedException("Access token is invalid or expired") from e

        for token, session in list(self.refresh_sessions.items()):
            if session.sub == subject:
                del self.refresh_sessions[token]

    async def verify_access_token(self, token: str, *, verify_exp: bool = True) -> dict[str, Any]:
        # Offline mock tokens are HS256 JWTs signed with the local secret.
        return decode_access_token(token, verify_exp=verify_exp)

    async def get_user_info(self, email: str) -> dict[str, str]:
        user = self.users.get(email)
        if not user:
            raise NotFoundException("User not found")
        return {"sub": user.sub, "name": user.full_name}


class AwsCognitoClient(CognitoClient):
    """Production AWS Cognito Identity Provider client using aioboto3."""

    def __init__(
        self,
        user_pool_id: str,
        client_id: str,
        region: str = "ap-southeast-1",
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_session_token: str | None = None,
        jwt_verifier: CognitoJwtVerifier | None = None,
    ) -> None:
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.region = region
        self.jwt_verifier = jwt_verifier or CognitoJwtVerifier(
            region=region,
            user_pool_id=user_pool_id,
            client_id=client_id,
        )
        session_kwargs: dict[str, str] = {"region_name": region}
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs["aws_access_key_id"] = aws_access_key_id
            session_kwargs["aws_secret_access_key"] = aws_secret_access_key
            if aws_session_token:
                session_kwargs["aws_session_token"] = aws_session_token
        self.session = aioboto3.Session(**session_kwargs)

    async def sign_up(self, email: str, password: str, full_name: str) -> dict[str, Any]:
        """Call AWS Cognito SignUp API with Username=email and UserAttributes."""
        async with self.session.client("cognito-idp", region_name=self.region) as client:
            try:
                response = await client.sign_up(
                    ClientId=self.client_id,
                    Username=email,
                    Password=password,
                    UserAttributes=[
                        {"Name": "email", "Value": email},
                        {"Name": "name", "Value": full_name},
                    ],
                )
                return {
                    "userSub": response.get("UserSub"),
                    "userConfirmed": response.get("UserConfirmed", False),
                    "status": "CONFIRMATION_REQUIRED",
                    "codeDeliveryDetails": response.get("CodeDeliveryDetails", {}),
                }
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                error_msg = e.response.get("Error", {}).get("Message", str(e))
                if error_code == "UsernameExistsException":
                    raise ConflictException("User account already exists") from e
                if error_code in ("InvalidPasswordException", "InvalidParameterException"):
                    raise ValidationException(error_msg) from e
                logger.error("Cognito sign_up ClientError: %s - %s", error_code, error_msg)
                raise BadGatewayException("Authentication provider error") from e

    async def confirm_sign_up(self, email: str, confirmation_code: str) -> dict[str, Any]:
        """Call AWS Cognito ConfirmSignUp API with confirmation OTP code."""
        async with self.session.client("cognito-idp", region_name=self.region) as client:
            try:
                await client.confirm_sign_up(
                    ClientId=self.client_id,
                    Username=email,
                    ConfirmationCode=confirmation_code,
                )
                return {"status": "CONFIRMED"}
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                error_msg = e.response.get("Error", {}).get("Message", str(e))
                if error_code in (
                    "CodeMismatchException",
                    "ExpiredCodeException",
                    "NotAuthorizedException",
                    "UserNotFoundException",
                ):
                    # Always enforce a valid OTP and return a uniform error so attackers
                    # cannot confirm accounts without a code or probe account status.
                    raise ValidationException("Invalid or expired confirmation code") from e
                logger.error("Cognito confirm_sign_up ClientError: %s - %s", error_code, error_msg)
                raise BadGatewayException("Authentication provider error") from e

    async def resend_confirmation_code(self, email: str) -> dict[str, Any]:
        """Call AWS Cognito ResendConfirmationCode API."""
        async with self.session.client("cognito-idp", region_name=self.region) as client:
            try:
                response = await client.resend_confirmation_code(
                    ClientId=self.client_id,
                    Username=email,
                )
                return {"codeDeliveryDetails": response.get("CodeDeliveryDetails", {})}
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                error_msg = e.response.get("Error", {}).get("Message", str(e))
                if error_code == "UserNotFoundException":
                    raise NotFoundException("User not found") from e
                if error_code == "InvalidParameterException":
                    raise ConflictException("User is already confirmed") from e
                if error_code in ("LimitExceededException", "TooManyRequestsException"):
                    raise TooManyRequestsException(
                        "Too many OTP requests. Please try again later."
                    ) from e
                logger.error(
                    "Cognito resend_confirmation ClientError: %s - %s",
                    error_code,
                    error_msg,
                )
                raise BadGatewayException("Authentication provider error") from e

    @staticmethod
    def _extract_auth_tokens(
        response: dict[str, Any],
        *,
        require_refresh_token: bool,
    ) -> dict[str, Any]:
        """Extract and validate Cognito AuthenticationResult token fields."""
        auth_result = response.get("AuthenticationResult")
        has_refresh = bool(auth_result and auth_result.get("RefreshToken"))
        if (
            not auth_result
            or not auth_result.get("AccessToken")
            or not auth_result.get("IdToken")
            or (require_refresh_token and not has_refresh)
        ):
            challenge_name = response.get("ChallengeName", "UNKNOWN_CHALLENGE")
            logger.warning(
                "Cognito initiate_auth did not return complete tokens (challenge=%s)",
                challenge_name,
            )
            raise UnauthorizedException(
                f"Additional authentication challenge required: {challenge_name}"
            )
        return {
            "accessToken": auth_result["AccessToken"],
            "idToken": auth_result["IdToken"],
            "refreshToken": auth_result.get("RefreshToken"),
            "expiresIn": auth_result.get("ExpiresIn", 3600),
        }

    async def authenticate(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate user credentials using InitiateAuth with USER_PASSWORD_AUTH."""
        async with self.session.client("cognito-idp", region_name=self.region) as client:
            try:
                # Server-side proxy uses USER_PASSWORD_AUTH over TLS because aioboto3 does
                # not implement Cognito SRP handshakes natively without external SRP libs.
                response = await client.initiate_auth(
                    ClientId=self.client_id,
                    AuthFlow="USER_PASSWORD_AUTH",
                    AuthParameters={
                        "USERNAME": email,
                        "PASSWORD": password,
                    },
                )
                return self._extract_auth_tokens(response, require_refresh_token=True)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                error_msg = e.response.get("Error", {}).get("Message", str(e))
                if error_code in ("NotAuthorizedException", "UserNotFoundException"):
                    raise UnauthorizedException("Incorrect username or password") from e
                if error_code == "UserNotConfirmedException":
                    raise UnauthorizedException("User is not confirmed. Please enter OTP") from e
                if error_code == "PasswordResetRequiredException":
                    raise UnauthorizedException("Password reset required before signing in") from e
                if error_code == "InvalidParameterException":
                    raise ValidationException(error_msg) from e
                if error_code in ("LimitExceededException", "TooManyRequestsException"):
                    raise TooManyRequestsException(
                        "Too many login attempts. Please try again later."
                    ) from e
                logger.error("Cognito authenticate ClientError: %s - %s", error_code, error_msg)
                raise BadGatewayException(f"Authentication provider error: {error_msg}") from e

    async def refresh_tokens(self, refresh_token: str) -> dict[str, Any]:
        """Exchange a Cognito refresh token for fresh AccessToken and IdToken."""
        async with self.session.client("cognito-idp", region_name=self.region) as client:
            try:
                response = await client.initiate_auth(
                    ClientId=self.client_id,
                    AuthFlow="REFRESH_TOKEN_AUTH",
                    AuthParameters={"REFRESH_TOKEN": refresh_token},
                )
                return self._extract_auth_tokens(response, require_refresh_token=False)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                error_msg = e.response.get("Error", {}).get("Message", str(e))
                if error_code in ("NotAuthorizedException", "UserNotFoundException"):
                    raise UnauthorizedException("Invalid or expired refresh token") from e
                if error_code == "InvalidParameterException":
                    raise ValidationException(error_msg) from e
                if error_code in ("LimitExceededException", "TooManyRequestsException"):
                    raise TooManyRequestsException(
                        "Too many token refresh requests. Please try again later."
                    ) from e
                logger.error("Cognito refresh_tokens ClientError: %s - %s", error_code, error_msg)
                raise BadGatewayException(f"Authentication provider error: {error_msg}") from e

    async def revoke_token(self, refresh_token: str) -> None:
        """Call Cognito RevokeToken for the given refresh token."""
        async with self.session.client("cognito-idp", region_name=self.region) as client:
            try:
                await client.revoke_token(Token=refresh_token, ClientId=self.client_id)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                error_msg = e.response.get("Error", {}).get("Message", str(e))
                # Only NotAuthorizedException proves the token is already dead. Other errors
                # (e.g. InvalidParameterException from a misconfigured client or token type)
                # must not look like a successful revocation.
                if error_code == "NotAuthorizedException":
                    raise UnauthorizedException("Invalid or expired refresh token") from e
                if error_code in ("LimitExceededException", "TooManyRequestsException"):
                    raise TooManyRequestsException(
                        "Too many sign-out requests. Please try again later."
                    ) from e
                logger.error("Cognito revoke_token ClientError: %s - %s", error_code, error_msg)
                # Provider detail stays in the log; clients only get a generic message.
                raise BadGatewayException("Authentication provider error") from e

    async def global_sign_out(self, access_token: str) -> None:
        """Call Cognito GlobalSignOut to invalidate all refresh tokens of the user."""
        async with self.session.client("cognito-idp", region_name=self.region) as client:
            try:
                await client.global_sign_out(AccessToken=access_token)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                error_msg = e.response.get("Error", {}).get("Message", str(e))
                if error_code == "NotAuthorizedException":
                    raise UnauthorizedException("Access token is invalid or expired") from e
                if error_code in ("LimitExceededException", "TooManyRequestsException"):
                    raise TooManyRequestsException(
                        "Too many sign-out requests. Please try again later."
                    ) from e
                logger.error("Cognito global_sign_out ClientError: %s - %s", error_code, error_msg)
                raise BadGatewayException("Authentication provider error") from e

    async def verify_access_token(self, token: str, *, verify_exp: bool = True) -> dict[str, Any]:
        """Verify a Cognito RS256 access token against the user pool's JWKS."""
        return await self.jwt_verifier.verify_access_token(token, verify_exp=verify_exp)

    @staticmethod
    def _extract_user_info(response: dict[str, Any]) -> dict[str, str]:
        """Extract sub and name attributes from an admin_get_user response."""
        attrs = {
            attr.get("Name"): str(attr.get("Value", ""))
            for attr in response.get("UserAttributes", [])
        }
        sub = attrs.get("sub", "")
        if not sub:
            raise NotFoundException("User sub attribute not found")
        return {"sub": sub, "name": attrs.get("name", "")}

    async def get_user_info(self, email: str) -> dict[str, str]:
        """Fetch user sub and name attributes via admin_get_user."""
        async with self.session.client("cognito-idp", region_name=self.region) as client:
            try:
                response = await client.admin_get_user(
                    UserPoolId=self.user_pool_id,
                    Username=email,
                )
                return self._extract_user_info(response)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                if error_code == "UserNotFoundException":
                    raise NotFoundException("User not found") from e
                error_msg = e.response.get("Error", {}).get("Message", str(e))
                logger.error("Cognito admin_get_user ClientError: %s - %s", error_code, error_msg)
                raise BadGatewayException("Authentication provider error") from e


_cognito_instance: CognitoClient | None = None


def _has_live_cognito_config(user_pool_id: str, client_id: str) -> bool:
    """Return True when both Cognito identifiers are non-placeholder live values."""
    return (
        bool(user_pool_id)
        and not user_pool_id.endswith("_local")
        and not user_pool_id.startswith("dummy")
        and bool(client_id)
        and not client_id.startswith("local_")
        and not client_id.startswith("dummy")
    )


def get_cognito_client() -> CognitoClient:
    """Retrieve singleton CognitoClient; fail fast outside local/test if unconfigured."""
    global _cognito_instance
    if _cognito_instance is None:
        settings = get_settings()
        has_live = _has_live_cognito_config(
            settings.cognito.user_pool_id,
            settings.cognito.client_id,
        )
        if not settings.app.is_local:
            if not has_live:
                raise RuntimeError(
                    "Live Cognito configuration is required outside local/test environments"
                )
            _cognito_instance = AwsCognitoClient(
                user_pool_id=settings.cognito.user_pool_id,
                client_id=settings.cognito.client_id,
                region=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            )
        elif settings.env != "test" and has_live:
            _cognito_instance = AwsCognitoClient(
                user_pool_id=settings.cognito.user_pool_id,
                client_id=settings.cognito.client_id,
                region=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            )
        else:
            _cognito_instance = MockCognitoClient()
    return _cognito_instance


def set_cognito_client(client: CognitoClient) -> None:
    """Explicitly override Cognito client for test dependency injection."""
    global _cognito_instance
    _cognito_instance = client
