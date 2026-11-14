"""Cognito Integration: Amazon Cognito User Pool Host Authentication.

Wraps SignUp, ConfirmSignUp, ResendConfirmationCode, InitiateAuth, and AdminGetUser
with automatic offline mock support for local and test environments.
"""

import logging
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
    UnauthorizedException,
    ValidationException,
)

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

    async def sign_up(self, email: str, password: str, full_name: str) -> dict[str, Any]:
        if email in self.users:
            raise ConflictException(f"User with email '{email}' already exists in Cognito")
        user_sub = str(uuid.uuid4())
        self.users[email] = CognitoUserRecord(
            sub=user_sub,
            email=email,
            password=password,
            full_name=full_name,
            is_confirmed=False,
            confirmation_code="123456",
        )
        logger.info("Mock Cognito sign_up for: %s (sub=%s)", email, user_sub)
        return {
            "userSub": user_sub,
            "userConfirmed": False,
            "status": "CONFIRMATION_REQUIRED",
            "codeDeliveryDetails": {"Destination": email, "DeliveryMedium": "EMAIL"},
        }

    async def confirm_sign_up(self, email: str, confirmation_code: str) -> dict[str, Any]:
        user = self.users.get(email)
        if not user:
            raise NotFoundException(f"User with email '{email}' not found")
        if confirmation_code != user.confirmation_code:
            raise ValidationException("Invalid confirmation code. Expected '123456'")
        user.is_confirmed = True
        logger.info("Mock Cognito confirmed sign_up for: %s", email)
        return {"status": "CONFIRMED", "sub": user.sub}

    async def resend_confirmation_code(self, email: str) -> dict[str, Any]:
        user = self.users.get(email)
        if not user:
            raise NotFoundException(f"User with email '{email}' not found")
        if user.is_confirmed:
            raise ConflictException("User is already confirmed")
        logger.info("Mock Cognito resend_confirmation_code for: %s", email)
        return {"codeDeliveryDetails": {"Destination": email, "DeliveryMedium": "EMAIL"}}

    async def authenticate(self, email: str, password: str) -> dict[str, Any]:
        user = self.users.get(email)
        if not user or user.password != password:
            raise UnauthorizedException("Incorrect username or password")
        if not user.is_confirmed:
            raise UnauthorizedException("User is not confirmed. Please enter OTP")

        from app.core.security import create_access_token

        access_token = create_access_token(
            subject=user.sub,
            claims={"email": user.email, "name": user.full_name},
        )
        return {
            "accessToken": access_token,
            "idToken": access_token,
            "refreshToken": f"mock_refresh_{user.sub}",
            "expiresIn": 3600,
        }

    async def get_user_info(self, email: str) -> dict[str, str]:
        user = self.users.get(email)
        if not user:
            raise NotFoundException(f"User with email '{email}' not found")
        return {"sub": user.sub, "name": user.full_name}


class AwsCognitoClient(CognitoClient):
    """Production AWS Cognito Identity Provider client using aioboto3."""

    def __init__(
        self,
        user_pool_id: str,
        client_id: str,
        region: str = "ap-southeast-1",
    ) -> None:
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.region = region
        self.session = aioboto3.Session()

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
                    raise ConflictException(f"User with email '{email}' already exists") from e
                if error_code in ("InvalidPasswordException", "InvalidParameterException"):
                    raise ValidationException(error_msg) from e
                logger.error("Cognito sign_up ClientError: %s - %s", error_code, error_msg)
                raise BadGatewayException(f"Authentication provider error: {error_msg}") from e

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
                    "NotAuthorizedException",
                    "CodeMismatchException",
                    "ExpiredCodeException",
                ):
                    # Support idempotent confirmation if user is already CONFIRMED in Cognito
                    try:
                        user_resp = await client.admin_get_user(
                            UserPoolId=self.user_pool_id,
                            Username=email,
                        )
                        if user_resp.get("UserStatus") == "CONFIRMED":
                            info = self._extract_user_info(user_resp, email)
                            return {"status": "CONFIRMED", **info}
                    except ClientError:
                        pass
                    if error_code == "NotAuthorizedException":
                        raise UnauthorizedException(error_msg) from e
                    raise ValidationException(error_msg) from e
                if error_code == "UserNotFoundException":
                    raise NotFoundException(f"User with email '{email}' not found") from e
                logger.error("Cognito confirm_sign_up ClientError: %s - %s", error_code, error_msg)
                raise BadGatewayException(f"Authentication provider error: {error_msg}") from e

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
                    raise NotFoundException(f"User with email '{email}' not found") from e
                if error_code == "InvalidParameterException":
                    raise ConflictException("User is already confirmed") from e
                logger.error(
                    "Cognito resend_confirmation ClientError: %s - %s",
                    error_code,
                    error_msg,
                )
                raise BadGatewayException(f"Authentication provider error: {error_msg}") from e

    async def authenticate(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate user credentials using InitiateAuth with USER_PASSWORD_AUTH."""
        async with self.session.client("cognito-idp", region_name=self.region) as client:
            try:
                response = await client.initiate_auth(
                    ClientId=self.client_id,
                    AuthFlow="USER_PASSWORD_AUTH",
                    AuthParameters={
                        "USERNAME": email,
                        "PASSWORD": password,
                    },
                )
                auth_result = response.get("AuthenticationResult", {})
                return {
                    "accessToken": auth_result.get("AccessToken"),
                    "idToken": auth_result.get("IdToken"),
                    "refreshToken": auth_result.get("RefreshToken"),
                    "expiresIn": auth_result.get("ExpiresIn", 3600),
                }
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                error_msg = e.response.get("Error", {}).get("Message", str(e))
                if error_code in ("NotAuthorizedException", "UserNotFoundException"):
                    raise UnauthorizedException("Incorrect username or password") from e
                if error_code == "UserNotConfirmedException":
                    raise UnauthorizedException("User is not confirmed. Please enter OTP") from e
                logger.error("Cognito authenticate ClientError: %s - %s", error_code, error_msg)
                raise BadGatewayException(f"Authentication provider error: {error_msg}") from e

    @staticmethod
    def _extract_user_info(response: dict[str, Any], email: str) -> dict[str, str]:
        """Extract sub and name attributes from an admin_get_user response."""
        attrs = {
            attr.get("Name"): str(attr.get("Value", ""))
            for attr in response.get("UserAttributes", [])
        }
        sub = attrs.get("sub", "")
        if not sub:
            raise NotFoundException(f"Sub attribute not found for user '{email}'")
        return {"sub": sub, "name": attrs.get("name", "")}

    async def get_user_info(self, email: str) -> dict[str, str]:
        """Fetch user sub and name attributes via admin_get_user."""
        async with self.session.client("cognito-idp", region_name=self.region) as client:
            try:
                response = await client.admin_get_user(
                    UserPoolId=self.user_pool_id,
                    Username=email,
                )
                return self._extract_user_info(response, email)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                if error_code == "UserNotFoundException":
                    raise NotFoundException(f"User with email '{email}' not found") from e
                error_msg = e.response.get("Error", {}).get("Message", str(e))
                raise BadGatewayException(f"Authentication provider error: {error_msg}") from e


_cognito_instance: CognitoClient | None = None


def get_cognito_client() -> CognitoClient:
    """Retrieve singleton CognitoClient instance (returns MockCognitoClient for local/test)."""
    global _cognito_instance
    if _cognito_instance is None:
        settings = get_settings()
        is_live_cognito = (
            not settings.app.is_local
            and bool(settings.cognito.user_pool_id)
            and not settings.cognito.user_pool_id.endswith("_local")
            and not settings.cognito.user_pool_id.startswith("dummy")
            and bool(settings.cognito.client_id)
            and not settings.cognito.client_id.startswith("local_")
            and not settings.cognito.client_id.startswith("dummy")
        )
        if is_live_cognito:
            _cognito_instance = AwsCognitoClient(
                user_pool_id=settings.cognito.user_pool_id,
                client_id=settings.cognito.client_id,
            )
        else:
            _cognito_instance = MockCognitoClient()
    return _cognito_instance


def set_cognito_client(client: CognitoClient) -> None:
    """Explicitly override Cognito client for test dependency injection."""
    global _cognito_instance
    _cognito_instance = client
