"""Room, RoomTranscript, and UsageLedger Async Repository.

Provides data access methods for Room sessions, compiled Transcripts, and Usage Ledgers.
"""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room, RoomTranscript, UsageLedger
from app.repositories.base import BaseRepository


class RoomRepository(BaseRepository[Room]):
    """Repository handling Room lifecycle, transcripts, and micro-billing ledger queries."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model_cls=Room)

    async def list_by_host(
        self,
        host_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[Room]:
        """Fetch rooms created by a specific host user ordered by creation time."""
        stmt = (
            select(Room)
            .where(Room.host_id == host_id)
            .order_by(Room.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_status(
        self,
        room_id: str,
        status: str,
        ended_at: datetime | None = None,
    ) -> Room | None:
        """Update active status of a room (e.g. ACTIVE, CLOSED)."""
        values: dict[str, str | datetime] = {"status": status}
        if ended_at is not None:
            values["ended_at"] = ended_at

        stmt = update(Room).where(Room.id == room_id).values(**values).returning(Room)
        result = await self.session.execute(stmt)
        updated = result.scalar_one_or_none()
        if updated:
            await self.session.flush()
        return updated

    async def get_transcript_by_room_id(self, room_id: str) -> RoomTranscript | None:
        """Fetch compiled transcript metadata record for a room."""
        stmt = select(RoomTranscript).where(RoomTranscript.room_id == room_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_transcript(self, transcript: RoomTranscript) -> RoomTranscript:
        """Persist or merge room transcript artifact metadata."""
        merged = await self.session.merge(transcript)
        await self.session.flush()
        return merged

    async def record_usage_ledger(self, ledger: UsageLedger) -> UsageLedger:
        """Record 10-second micro-billing ledger entry."""
        self.session.add(ledger)
        await self.session.flush()
        await self.session.refresh(ledger)
        return ledger

    async def list_usage_ledgers(self, room_id: str) -> Sequence[UsageLedger]:
        """List all 10-second micro-billing ledger entries for a room."""
        stmt = (
            select(UsageLedger)
            .where(UsageLedger.room_id == room_id)
            .order_by(UsageLedger.interval_index.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
