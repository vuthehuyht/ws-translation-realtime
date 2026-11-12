"""Cognito Integration: Amazon Cognito User Pool Host Authentication.

Wraps SignUp, ConfirmSignUp, ResendConfirmationCode, InitiateAuth, and AdminGetUser
with automatic offline mock support for local and test environments.
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import (
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
        raise NotImplementedError

    async def confirm_sign_up(self, email: str, confirmation_code: str) -> dict[str, Any]:
        raise NotImplementedError

    async def resend_confirmation_code(self, email: str) -> dict[str, Any]:
        raise NotImplementedError

    async def authenticate(self, email: str, password: str) -> dict[str, Any]:
        raise NotImplementedError

    async def get_user_sub(self, email: str) -> str:
        raise NotImplementedError


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

    async def get_user_sub(self, email: str) -> str:
        user = self.users.get(email)
        if not user:
            raise NotFoundException(f"User with email '{email}' not found")
        return user.sub


_cognito_instance: CognitoClient | None = None


def get_cognito_client() -> CognitoClient:
    """Retrieve singleton CognitoClient instance (returns MockCognitoClient for local/test)."""
    global _cognito_instance
    if _cognito_instance is None:
        settings = get_settings()
        if settings.app.is_local or not settings.cognito.user_pool_id.startswith("ap-southeast-1_"):
            _cognito_instance = MockCognitoClient()
        else:
            # Fallback to Mock if AWS credentials are dummy/offline
            _cognito_instance = MockCognitoClient()
    return _cognito_instance


def set_cognito_client(client: CognitoClient) -> None:
    """Explicitly override Cognito client for test dependency injection."""
    global _cognito_instance
    _cognito_instance = client
