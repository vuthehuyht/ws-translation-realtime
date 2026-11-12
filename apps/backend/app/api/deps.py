"""FastAPI Route Dependencies: Database Sessions, Authentication, and Repositories/Services.

Provides dependency injection for async database transactions, JWT bearer validation,
repositories, domain services, and Redis connection pooling across REST endpoints.
"""

from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.room_repository import RoomRepository
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.auth_service import AuthService
from app.services.wallet_service import WalletService

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Yield or initialize singleton async Redis client."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = aioredis.from_url(
            settings.redis.url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


# Repository dependencies
def get_user_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    """Provide UserRepository instance bound to current AsyncSession."""
    return UserRepository(session=db)


def get_wallet_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WalletRepository:
    """Provide WalletRepository instance bound to current AsyncSession."""
    return WalletRepository(session=db)


def get_room_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoomRepository:
    """Provide RoomRepository instance bound to current AsyncSession."""
    return RoomRepository(session=db)


# Service dependencies
def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    wallet_repo: Annotated[WalletRepository, Depends(get_wallet_repository)],
) -> AuthService:
    """Provide AuthService instance wired with user and wallet repositories."""
    return AuthService(user_repo=user_repo, wallet_repo=wallet_repo)


def get_wallet_service(
    wallet_repo: Annotated[WalletRepository, Depends(get_wallet_repository)],
) -> WalletService:
    """Provide WalletService instance wired with wallet repository."""
    return WalletService(wallet_repo=wallet_repo)


# User authentication dependencies
def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Extract and validate the JWT Bearer token, returning the user's sub identifier."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or malformed Authorization header")

    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Token payload missing subject identifier")
        return user_id
    except ValueError as e:
        raise UnauthorizedException(str(e)) from e


async def get_current_user(
    user_id: Annotated[str, Depends(get_current_user_id)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """Retrieve the full User ORM model via UserRepository for the authenticated subject."""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedException("User does not exist or has been removed")
    if user.status == "SUSPENDED":
        raise ForbiddenException("User account is currently suspended")
    return user
