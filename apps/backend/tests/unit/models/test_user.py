"""Unit tests for User and UserProfile ORM models (app.models.user)."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, UserProfile


async def test_create_user_and_profile_relationship(db_session: AsyncSession) -> None:
    user_id = "test-cognito-sub-12345"
    user = User(
        id=user_id,
        email="host@example.com",
        role="HOST",
        status="ACTIVE",
    )
    profile = UserProfile(
        user_id=user_id,
        full_name="Nguyễn Văn A",
        default_source_lang="vi-VN",
        default_target_langs=["en-US", "ja-JP"],
        timezone="Asia/Ho_Chi_Minh",
    )
    db_session.add(user)
    db_session.add(profile)
    await db_session.flush()

    stmt = select(User).options(selectinload(User.profile)).where(User.id == user_id)
    result = await db_session.execute(stmt)
    fetched_user = result.scalar_one()

    assert fetched_user.email == "host@example.com"
    assert fetched_user.profile is not None
    assert fetched_user.profile.full_name == "Nguyễn Văn A"
    assert fetched_user.profile.default_target_langs == ["en-US", "ja-JP"]


async def test_delete_user_does_not_load_lazy_raise_relationships(
    db_session: AsyncSession,
) -> None:
    db_session.add(User(id="sub-del", email="delete@example.com"))
    await db_session.flush()
    user = (await db_session.execute(select(User).where(User.id == "sub-del"))).scalar_one()

    # With passive_deletes=True this must not raise InvalidRequestError from lazy="raise".
    await db_session.delete(user)
    await db_session.flush()

    remaining = await db_session.execute(select(User).where(User.id == "sub-del"))
    assert remaining.scalar_one_or_none() is None


async def test_duplicate_email_violates_unique_constraint(db_session: AsyncSession) -> None:
    user1 = User(id="sub-1", email="duplicate@example.com")
    user2 = User(id="sub-2", email="duplicate@example.com")
    db_session.add(user1)
    await db_session.flush()

    db_session.add(user2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()
