"""Unit tests for UserRepository (app.repositories.user_repository)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserProfile
from app.repositories.user_repository import UserRepository


async def test_user_repository_create_and_find_by_email(db_session: AsyncSession) -> None:
    repo = UserRepository(session=db_session)
    user_id = "cognito-sub-uuid-101"

    user = User(
        id=user_id,
        email="john.doe@example.com",
        role="HOST",
        status="ACTIVE",
    )
    profile = UserProfile(
        user_id=user_id,
        full_name="John Doe",
        default_source_lang="en-US",
        default_target_langs=["vi-VN"],
    )

    created_user = await repo.create_user_with_profile(user, profile)
    assert created_user.id == user_id
    assert created_user.email == "john.doe@example.com"

    # Find by email (case insensitive)
    fetched = await repo.get_by_email("JOHN.DOE@EXAMPLE.COM")
    assert fetched is not None
    assert fetched.id == user_id
    assert fetched.profile is not None
    assert fetched.profile.full_name == "John Doe"


async def test_user_repository_update_profile(db_session: AsyncSession) -> None:
    repo = UserRepository(session=db_session)
    user_id = "cognito-sub-uuid-102"

    user = User(id=user_id, email="update.test@example.com")
    profile = UserProfile(user_id=user_id, full_name="Original Name")
    await repo.create_user_with_profile(user, profile)

    # Update profile fields
    updated_profile = await repo.update_profile(
        user_id=user_id,
        full_name="Updated Name",
        timezone="Asia/Tokyo",
    )
    assert updated_profile is not None
    assert updated_profile.full_name == "Updated Name"
    assert updated_profile.timezone == "Asia/Tokyo"

    # Query back
    fetched = await repo.get_by_id(user_id)
    assert fetched is not None
    assert fetched.profile.full_name == "Updated Name"
