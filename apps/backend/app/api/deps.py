"""FastAPI Route Dependencies: Database Sessions, Authentication, and Repositories/Services.

Provides dependency injection for async database transactions, JWT bearer validation,
repositories, domain services, and Redis connection pooling across REST endpoints.
"""

from dataclasses import dataclass
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.integrations.cognito import get_cognito_client
from app.models.user import User
from app.repositories.room_repository import RoomRepository
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository
from app.services import token_blocklist
from app.services.auth_service import AuthService
from app.services.wallet_service import WalletService

_redis_client: aioredis.Redis | None = None

REDIS_CONNECT_TIMEOUT_SECONDS = 2.0
REDIS_SOCKET_TIMEOUT_SECONDS = 2.0


async def get_redis() -> aioredis.Redis:
    """Yield or initialize singleton async Redis client."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = aioredis.from_url(
            settings.redis.url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=REDIS_CONNECT_TIMEOUT_SECONDS,
            socket_timeout=REDIS_SOCKET_TIMEOUT_SECONDS,
            retry_on_timeout=False,
        )
    return _redis_client


async def close_redis_connection() -> None:
    """Close singleton async Redis connection pool on application shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


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
    redis_client: Annotated[aioredis.Redis, Depends(get_redis)],
) -> AuthService:
    """Provide AuthService instance wired with user, wallet repositories, and Redis."""
    return AuthService(
        user_repo=user_repo,
        wallet_repo=wallet_repo,
        redis_client=redis_client,
    )


def get_wallet_service(
    wallet_repo: Annotated[WalletRepository, Depends(get_wallet_repository)],
) -> WalletService:
    """Provide WalletService instance wired with wallet repository."""
    return WalletService(wallet_repo=wallet_repo)


# User authentication dependencies
@dataclass(frozen=True, slots=True)
class AccessTokenContext:
    """Validated, non-revoked access token and the claims endpoints need from it."""

    token: str
    subject: str
    issued_at: int | None
    expires_at: int | None
    # Cognito `origin_jti`: identifies the login session that minted this token.
    session_id: str | None = None


async def _build_token_context(
    redis_client: aioredis.Redis,
    authorization: str | None,
    *,
    verify_exp: bool,
) -> AccessTokenContext:
    """Validate the Bearer JWT signature and reject tokens revoked by logout."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or malformed Authorization header")

    token = authorization.split(" ", 1)[1]
    try:
        # Real Cognito tokens are RS256 (verified via JWKS); offline mode uses local HS256.
        payload = await get_cognito_client().verify_access_token(token, verify_exp=verify_exp)
    except ValueError as e:
        raise UnauthorizedException(str(e)) from e

    subject: str | None = payload.get("sub")
    if not subject:
        raise UnauthorizedException("Token payload missing subject identifier")

    issued_at = payload.get("iat")
    expires_at = payload.get("exp")
    origin_jti = payload.get("origin_jti")
    context = AccessTokenContext(
        token=token,
        subject=subject,
        issued_at=issued_at if isinstance(issued_at, int) else None,
        expires_at=expires_at if isinstance(expires_at, int) else None,
        session_id=origin_jti if isinstance(origin_jti, str) and origin_jti else None,
    )
    # Fail-closed: this runs before any Cognito call, so during a Redis outage even logout
    # returns 503 rather than risk honouring a revoked token.
    if await token_blocklist.is_revoked(
        redis_client,
        token=token,
        subject=subject,
        issued_at=context.issued_at,
        session_id=context.session_id,
    ):
        raise UnauthorizedException("Token has been revoked")
    return context


async def get_access_token_context(
    redis_client: Annotated[aioredis.Redis, Depends(get_redis)],
    authorization: Annotated[str | None, Header()] = None,
) -> AccessTokenContext:
    """Authenticate a request: valid signature, not expired, not revoked."""
    return await _build_token_context(redis_client, authorization, verify_exp=True)


async def get_logout_token_context(
    redis_client: Annotated[aioredis.Redis, Depends(get_redis)],
    authorization: Annotated[str | None, Header()] = None,
) -> AccessTokenContext:
    """Like get_access_token_context but tolerates an expired token.

    A user with a stale tab must still be able to revoke the refresh cookie on logout.
    """
    return await _build_token_context(redis_client, authorization, verify_exp=False)


async def get_current_user_id(
    context: Annotated[AccessTokenContext, Depends(get_access_token_context)],
) -> str:
    """Return the sub identifier of the authenticated, non-revoked access token."""
    return context.subject


async def get_current_user(
    user_id: Annotated[str, Depends(get_current_user_id)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """Retrieve the full User ORM model via UserRepository for the authenticated subject."""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedException("User does not exist or has been removed")
    if user.status != "ACTIVE":
        raise ForbiddenException("User account is not active or is suspended")
    return user
