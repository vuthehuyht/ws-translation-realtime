"""Unit tests for AuthService.logout guard rails (TASK-AUTH-08)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ServiceUnavailableException
from app.integrations.cognito import MockCognitoClient
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.auth_service import AuthService


async def test_logout_requires_session_store(db_session: AsyncSession) -> None:
    service = AuthService(
        user_repo=UserRepository(session=db_session),
        wallet_repo=WalletRepository(session=db_session),
        cognito_client=MockCognitoClient(),
        redis_client=None,
    )

    # Returning success without a blocklist would claim a revocation that is not enforced.
    with pytest.raises(ServiceUnavailableException):
        await service.logout(
            access_token="t",
            subject="u1",
            expires_at=None,
            refresh_token="r",
            global_sign_out=False,
        )
