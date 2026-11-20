"""User, UserProfile, and DeletedAccountRecord Async Repository.

Provides data access methods for User, UserProfile, and GDPR deletion cooldown records.
"""

import hashlib
import hmac
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.user import DeletedAccountRecord, User, UserProfile
from app.repositories.base import BaseRepository


def hash_email(email: str) -> str:
    """Return a server-peppered HMAC-SHA256 hex digest of a normalized lowercase email."""
    pepper = get_settings().security.effective_email_hash_pepper
    normalized = email.strip().lower()
    return hmac.new(
        pepper.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class UserRepository(BaseRepository[User]):
    """Repository handling User and UserProfile database queries."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model_cls=User)

    async def get_by_id(
        self,
        entity_id: Any,
        *,
        include_profile: bool = False,
        include_wallet: bool = False,
        for_update: bool = False,
    ) -> User | None:
        """Fetch a user by primary key, optionally eager-loading UserProfile and Wallet."""
        stmt = select(User).where(User.id == entity_id)
        if for_update:
            stmt = stmt.with_for_update()
        if include_profile:
            stmt = stmt.options(selectinload(User.profile))
        if include_wallet:
            stmt = stmt.options(selectinload(User.wallet))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        email: str,
        *,
        include_profile: bool = False,
    ) -> User | None:
        """Find a user by normalized lowercase email, optionally eager-loading UserProfile."""
        stmt = select(User).where(User.email == email.strip().lower())
        if include_profile:
            stmt = stmt.options(selectinload(User.profile))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user_with_profile(
        self,
        user: User,
        profile: UserProfile,
    ) -> User:
        """Persist a User and associated UserProfile atomically in the current transaction."""
        self.session.add(user)
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_profile(
        self,
        user_id: str,
        **kwargs: Any,
    ) -> UserProfile | None:
        """Update UserProfile fields dynamically."""
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.session.execute(stmt)
        profile = result.scalar_one_or_none()
        if not profile:
            return None

        for field, value in kwargs.items():
            if hasattr(profile, field):
                setattr(profile, field, value)

        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def get_deleted_account_by_email_hash(
        self,
        email_hash: str,
    ) -> DeletedAccountRecord | None:
        """Look up a prior deleted-account record by hashed lowercase email."""
        stmt = select(DeletedAccountRecord).where(DeletedAccountRecord.email_hash == email_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_deleted_account_record(
        self,
        *,
        email_hash: str,
        deleted_at: datetime,
        re_register_allowed_at: datetime,
    ) -> DeletedAccountRecord:
        """Create or update a deleted-account record for 7-day cooldown and bonus gating."""
        existing = await self.get_deleted_account_by_email_hash(email_hash)
        if existing is not None:
            existing.deleted_at = deleted_at
            existing.re_register_allowed_at = re_register_allowed_at
            existing.deletion_count += 1
            await self.session.flush()
            await self.session.refresh(existing)
            return existing

        record = DeletedAccountRecord(
            email_hash=email_hash,
            deleted_at=deleted_at,
            re_register_allowed_at=re_register_allowed_at,
            deletion_count=1,
        )
        try:
            async with self.session.begin_nested():
                self.session.add(record)
                await self.session.flush()
            await self.session.refresh(record)
            return record
        except IntegrityError:
            existing = await self.get_deleted_account_by_email_hash(email_hash)
            if existing is None:
                raise
            existing.deleted_at = deleted_at
            existing.re_register_allowed_at = re_register_allowed_at
            existing.deletion_count += 1
            await self.session.flush()
            await self.session.refresh(existing)
            return existing

    async def anonymize_user_account(self, user_or_id: User | str) -> bool:
        """Scrub all PII while preserving the user row so financial ledgers remain intact."""
        user = (
            user_or_id
            if isinstance(user_or_id, User)
            else await self.get_by_id(user_or_id, include_profile=True, include_wallet=True)
        )
        if user is None:
            return False

        # Replace email with a non-routable placeholder so the original email is removed from PII
        # and can be re-registered after the 7-day cooldown window.
        user.status = "DELETED"
        user.email = f"deleted_{user.id}@anonymized.invalid"

        if user.profile is not None:
            user.profile.full_name = "Deleted User"
            user.profile.phone_number = None
            user.profile.bio = None
            user.profile.avatar_url = None
            user.profile.company_name = None
            user.profile.tax_code = None
            user.profile.company_address = None
            user.profile.stripe_customer_id = None
            user.profile.preferences = {}

        if user.wallet is not None:
            user.wallet.auto_topup_enabled = False
            user.wallet.default_payment_method_id = None

        await self.session.flush()
        return True
