"""Unit tests for UserRepository (app.repositories.user_repository)."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy import event
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserProfile
from app.models.wallet import Wallet
from app.repositories.user_repository import UserRepository, hash_email


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


def test_hash_email_normalizes_case_and_whitespace() -> None:
    import hashlib

    digest = hash_email("User.Name@Example.COM")
    assert len(digest) == 64
    assert digest == hash_email("  user.name@example.com  ")
    assert digest != hash_email("other@example.com")
    # Must be peppered HMAC-SHA256, never plain unsalted SHA-256
    assert digest != hashlib.sha256(b"user.name@example.com").hexdigest()


async def test_user_repository_deleted_account_record_upsert_and_lookup(
    db_session: AsyncSession,
) -> None:
    repo = UserRepository(session=db_session)
    email_hash = hash_email("deleted.repo@example.com")

    assert await repo.get_deleted_account_by_email_hash(email_hash) is None

    first_deleted_at = datetime.now(UTC) - timedelta(days=10)
    first_allowed_at = first_deleted_at + timedelta(days=7)
    created = await repo.upsert_deleted_account_record(
        email_hash=email_hash,
        deleted_at=first_deleted_at,
        re_register_allowed_at=first_allowed_at,
    )
    assert created.email_hash == email_hash
    assert created.deletion_count == 1

    # Second deletion for the same email hash updates in place and increments deletion_count
    second_deleted_at = datetime.now(UTC)
    second_allowed_at = second_deleted_at + timedelta(days=7)
    updated = await repo.upsert_deleted_account_record(
        email_hash=email_hash,
        deleted_at=second_deleted_at,
        re_register_allowed_at=second_allowed_at,
    )
    assert updated.id == created.id
    assert updated.deletion_count == 2

    fetched = await repo.get_deleted_account_by_email_hash(email_hash)
    assert fetched is not None
    assert fetched.deletion_count == 2


async def test_user_repository_anonymize_user_account_scrubs_pii_and_keeps_wallet(
    db_session: AsyncSession,
) -> None:
    repo = UserRepository(session=db_session)
    user_id = "cognito-sub-anonymize-1"

    user = User(id=user_id, email="pii.host@example.com", role="HOST", status="ACTIVE")
    profile = UserProfile(
        user_id=user_id,
        full_name="Sensitive Name",
        phone_number="+84901234567",
        bio="Personal bio",
        avatar_url="https://cdn.example.com/avatars/1.png",
        company_name="Private Co",
        tax_code="0101234567",
        company_address="123 Secret St",
        stripe_customer_id="cus_12345",
        preferences={"vadSensitivity": "high"},
    )
    await repo.create_user_with_profile(user, profile)
    db_session.add(
        Wallet(
            host_id=user_id,
            balance=Decimal("12.5000"),
            currency="USD",
            auto_topup_enabled=True,
            default_payment_method_id="pm_card_123",
        )
    )
    await db_session.flush()

    assert await repo.anonymize_user_account("non-existent-id") is False
    assert await repo.anonymize_user_account(user_id) is True

    db_session.expire_all()
    anonymized = await repo.get_by_id(user_id, include_profile=True, include_wallet=True)
    assert anonymized is not None
    assert anonymized.status == "DELETED"
    assert anonymized.email == f"deleted_{user_id}@anonymized.invalid"
    assert anonymized.profile.full_name == "Deleted User"
    assert anonymized.profile.phone_number is None
    assert anonymized.profile.bio is None
    assert anonymized.profile.avatar_url is None
    assert anonymized.profile.company_name is None
    assert anonymized.profile.tax_code is None
    assert anonymized.profile.company_address is None
    assert anonymized.profile.stripe_customer_id is None
    assert anonymized.profile.preferences == {}
    assert anonymized.wallet.auto_topup_enabled is False
    assert anonymized.wallet.default_payment_method_id is None
    # Balance stays intact for accounting audit trail
    assert anonymized.wallet.balance == Decimal("12.5000")
