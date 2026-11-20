"""User and UserProfile Async Repository.

Provides data access methods for User and UserProfile database entities.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, UserProfile
from app.repositories.base import BaseRepository


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
    ) -> User | None:
        """Fetch a user by primary key, optionally eager-loading UserProfile and Wallet."""
        stmt = select(User).where(User.id == entity_id)
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
