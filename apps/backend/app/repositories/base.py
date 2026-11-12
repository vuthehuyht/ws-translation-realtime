"""Generic Async SQLAlchemy 2.0 Base Repository.

Provides reusable async CRUD operations encapsulating AsyncSession queries.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base


class BaseRepository[ModelType: Base]:
    """Generic async repository encapsulating common database operations."""

    def __init__(self, session: AsyncSession, model_cls: type[ModelType]) -> None:
        self.session = session
        self.model_cls = model_cls

    async def get_by_id(self, entity_id: Any) -> ModelType | None:
        """Fetch a single entity by its primary key ID."""
        stmt = select(self.model_cls).where(self.model_cls.id == entity_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """Fetch a paginated list of entities."""
        stmt = select(self.model_cls).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, entity: ModelType) -> ModelType:
        """Add and flush a new entity to the active session."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: ModelType) -> ModelType:
        """Merge/update an entity and flush changes."""
        merged = await self.session.merge(entity)
        await self.session.flush()
        return merged

    async def delete_by_id(self, entity_id: Any) -> bool:
        """Delete an entity by its primary key ID."""
        stmt = delete(self.model_cls).where(self.model_cls.id == entity_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[attr-defined, no-any-return]

    async def count(self) -> int:
        """Count the total number of records for the model."""
        stmt = select(func.count()).select_from(self.model_cls)
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0
