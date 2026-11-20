"""Unit Tests for UserService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.user import User, UserProfile
from app.repositories.user_repository import UserRepository
from app.schemas.requests.user import AvatarConfirmRequest, UpdateProfileRequest
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
