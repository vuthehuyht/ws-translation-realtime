"""Unit Tests for UserService."""

from unittest.mock import AsyncMock

import fakeredis.aioredis
import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadGatewayException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ServiceUnavailableException,
)
from app.integrations.cognito import get_cognito_client
from app.integrations.s3 import get_s3_client
from app.models.room import Room
from app.models.user import User, UserProfile
from app.repositories.room_repository import RoomRepository
from app.repositories.user_repository import UserRepository, hash_email
from app.schemas.requests.user import AvatarConfirmRequest, UpdateProfileRequest
from app.services import token_blocklist
from app.services.user_service import UserService

pytestmark = pytest.mark.asyncio


async def test_get_me_raises_not_found_for_unknown_user(db_session: AsyncSession) -> None:
    service = UserService(user_repo=UserRepository(session=db_session))
    with pytest.raises(NotFoundException):
        await service.get_me("missing-user-id")


async def test_confirm_avatar_blocks_path_traversal(db_session: AsyncSession) -> None:
    repo = UserRepository(session=db_session)
    user = User(id="user-1", email="u1@example.com", role="HOST", status="ACTIVE")
    profile = UserProfile(user_id="user-1", full_name="User One")
    await repo.create_user_with_profile(user, profile)
    await db_session.commit()

    service = UserService(user_repo=repo)
    with pytest.raises(ForbiddenException):
        await service.confirm_avatar(
            "user-1",
            AvatarConfirmRequest(s3_key="avatars/user-1/../user-2/evil.png"),
        )


async def test_update_profile_clears_optional_fields_when_null(
    db_session: AsyncSession,
) -> None:
    repo = UserRepository(session=db_session)
    user = User(id="user-2", email="u2@example.com", role="HOST", status="ACTIVE")
    profile = UserProfile(
        user_id="user-2",
        full_name="User Two",
        phone_number="+84901234567",
        bio="Initial bio",
    )
    await repo.create_user_with_profile(user, profile)
    await db_session.commit()

    service = UserService(user_repo=repo)
    result = await service.update_profile(
        "user-2",
        UpdateProfileRequest(phone_number=None, bio=None),
    )
    assert result.full_name == "User Two"
    assert result.phone_number is None
    assert result.bio is None


async def test_delete_account_raises_not_found_for_unknown_user(
    db_session: AsyncSession,
) -> None:
    service = UserService(
        user_repo=UserRepository(session=db_session),
        room_repo=RoomRepository(session=db_session),
    )
    with pytest.raises(NotFoundException):
        await service.delete_account(
            user_id="missing-user",
            access_token="token",
            expires_at=None,
        )


async def test_delete_account_blocks_when_user_has_active_room(
    db_session: AsyncSession,
) -> None:
    user_repo = UserRepository(session=db_session)
    room_repo = RoomRepository(session=db_session)
    user = User(id="user-3", email="u3@example.com", role="HOST", status="ACTIVE")
    profile = UserProfile(user_id="user-3", full_name="User Three")
    await user_repo.create_user_with_profile(user, profile)
    db_session.add(
        Room(
            id="room-3",
            host_id="user-3",
            title="Active Session",
            status="ACTIVE",
            host_token_hash="hash",
        )
    )
    await db_session.commit()

    service = UserService(user_repo=user_repo, room_repo=room_repo)
    with pytest.raises(ConflictException, match="active translation rooms"):
        await service.delete_account(
            user_id="user-3",
            access_token="token",
            expires_at=None,
        )


async def test_delete_account_fails_closed_when_room_repo_missing(
    db_session: AsyncSession,
) -> None:
    service = UserService(user_repo=UserRepository(session=db_session), room_repo=None)
    with pytest.raises(ServiceUnavailableException):
        await service.delete_account(
            user_id="any-user",
            access_token="token",
            expires_at=None,
        )


async def test_delete_account_rolls_back_db_when_cognito_fails(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_repo = UserRepository(session=db_session)
    room_repo = RoomRepository(session=db_session)
    user = User(id="user-rollback", email="rollback@example.com", role="HOST", status="ACTIVE")
    profile = UserProfile(user_id="user-rollback", full_name="Rollback Host")
    await user_repo.create_user_with_profile(user, profile)
    await db_session.commit()

    cognito = get_cognito_client()
    monkeypatch.setattr(
        cognito,
        "delete_user",
        AsyncMock(side_effect=BadGatewayException("Cognito outage")),
    )

    service = UserService(user_repo=user_repo, room_repo=room_repo)
    with pytest.raises(BadGatewayException, match="Cognito outage"):
        await service.delete_account(
            user_id="user-rollback",
            access_token="token",
            expires_at=None,
        )

    db_session.expire_all()
    persisted = await user_repo.get_by_id("user-rollback", include_profile=True)
    assert persisted is not None
    assert persisted.status == "ACTIVE"
    assert persisted.email == "rollback@example.com"
    assert persisted.profile.full_name == "Rollback Host"
    deleted_record = await user_repo.get_deleted_account_by_email_hash(
        hash_email("rollback@example.com")
    )
    assert deleted_record is None


async def test_delete_account_happy_path_and_tolerates_redis_and_s3_errors(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cognito = get_cognito_client()
    email = "svc.delete@example.com"
    password = "ValidPassword123!"  # noqa: S105
    signup = await cognito.sign_up(email=email, password=password, full_name="Svc Delete")
    await cognito.confirm_sign_up(email=email, confirmation_code="123456")
    tokens = await cognito.authenticate(email=email, password=password)
    user_id = signup["userSub"]

    user_repo = UserRepository(session=db_session)
    room_repo = RoomRepository(session=db_session)
    await user_repo.create_user_with_profile(
        User(id=user_id, email=email, role="HOST", status="ACTIVE"),
        UserProfile(user_id=user_id, full_name="Svc Delete", bio="Secret"),
    )
    await db_session.commit()

    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    s3 = get_s3_client()
    await s3.upload_bytes(f"avatars/{user_id}/pic.png", b"img", content_type="image/png")

    service = UserService(user_repo=user_repo, room_repo=room_repo, redis_client=fake_redis)
    await service.delete_account(
        user_id=user_id,
        access_token=tokens["accessToken"],
        expires_at=None,
    )

    assert await s3.object_exists(f"avatars/{user_id}/pic.png") is False
    assert (
        await token_blocklist.is_revoked(
            fake_redis,
            token=tokens["accessToken"],
            subject=user_id,
            issued_at=None,
        )
        is True
    )
    assert await user_repo.get_deleted_account_by_email_hash(hash_email(email)) is not None
    await fake_redis.aclose()

    # Second user: Redis and S3 post-commit cleanup failures must not turn deletion into 5xx
    email2 = "svc.delete2@example.com"
    signup2 = await cognito.sign_up(email=email2, password=password, full_name="Svc Delete 2")
    await cognito.confirm_sign_up(email=email2, confirmation_code="123456")
    tokens2 = await cognito.authenticate(email=email2, password=password)
    user_id2 = signup2["userSub"]

    await user_repo.create_user_with_profile(
        User(id=user_id2, email=email2, role="HOST", status="ACTIVE"),
        UserProfile(user_id=user_id2, full_name="Svc Delete 2"),
    )
    await db_session.commit()

    broken_redis = AsyncMock()
    broken_redis.set.side_effect = RedisConnectionError("Redis offline")
    monkeypatch.setattr(s3, "delete_prefix", AsyncMock(side_effect=BadGatewayException("S3 down")))

    service2 = UserService(user_repo=user_repo, room_repo=room_repo, redis_client=broken_redis)
    await service2.delete_account(
        user_id=user_id2,
        access_token=tokens2["accessToken"],
        expires_at=None,
    )

    db_session.expire_all()
    user2 = await user_repo.get_by_id(user_id2)
    assert user2 is not None
    assert user2.status == "DELETED"
