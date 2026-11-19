"""Unit tests for UserRepository (app.repositories.user_repository)."""

from typing import Any

import pytest
from sqlalchemy import event
from sqlalchemy.exc import InvalidRequestError
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

    # Find by email (case insensitive) with explicit profile loading
    fetched = await repo.get_by_email("JOHN.DOE@EXAMPLE.COM", include_profile=True)
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

    # Query back with explicit profile loading
    fetched = await repo.get_by_id(user_id, include_profile=True)
    assert fetched is not None
    assert fetched.profile.full_name == "Updated Name"


async def test_user_repository_avoids_unnecessary_relationship_queries(
    db_session: AsyncSession,
) -> None:
    """Verify User lookups emit 1 SQL query by default and 2 when include_profile=True."""
    repo = UserRepository(session=db_session)
    user_id = "cognito-sub-uuid-query-count"

    await repo.create_user_with_profile(
        User(id=user_id, email="query.count@example.com"),
        UserProfile(user_id=user_id, full_name="Query Counter"),
    )
    db_session.expire_all()

    executed_sql: list[str] = []
    sync_engine = db_session.get_bind()

    def _record_sql(_conn: Any, _cursor: Any, statement: str, *_args: Any) -> None:
        if statement.lstrip().upper().startswith("SELECT"):
            executed_sql.append(statement)

    event.listen(sync_engine, "before_cursor_execute", _record_sql)
    try:
        # Default lookup should emit exactly 1 SELECT (users only)
        user_only = await repo.get_by_email("query.count@example.com")
        assert user_only is not None
        assert len(executed_sql) == 1
        with pytest.raises(InvalidRequestError):
            _ = user_only.profile

        # Explicit include_profile=True should emit exactly 2 SELECTs (users + user_profiles)
        db_session.expire_all()
        executed_sql.clear()
        user_with_profile = await repo.get_by_email(
            "query.count@example.com", include_profile=True
        )
        assert user_with_profile is not None
        assert len(executed_sql) == 2
        assert user_with_profile.profile.full_name == "Query Counter"
        with pytest.raises(InvalidRequestError):
            _ = user_with_profile.wallet
    finally:
        event.remove(sync_engine, "before_cursor_execute", _record_sql)
