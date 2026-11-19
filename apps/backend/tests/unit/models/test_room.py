"""Unit tests for Room, RoomTranscript, and UsageLedger ORM models (app.models.room)."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room, RoomTranscript, UsageLedger
from app.models.user import User


async def test_room_lifecycle_and_usage_ledger(db_session: AsyncSession) -> None:
    user_id = "room-host-sub"
    room_id = "test-room-uuid"
    user = User(id=user_id, email="room_host@example.com")
    room = Room(
        id=room_id,
        host_id=user_id,
        title="Quarterly Review 2026",
        source_language="vi-VN",
        target_languages=["en-US"],
        status="ACTIVE",
        host_token_hash="hash123",
        started_at=datetime.now(UTC),
    )
    transcript = RoomTranscript(
        room_id=room_id,
        s3_key_master=f"transcripts/{room_id}/master.json",
        summary_status="READY",
        summary_cost_usd=Decimal("0.0500"),
    )
    ledger = UsageLedger(
        room_id=room_id,
        interval_index=1,
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC),
        audio_seconds=Decimal("10.00"),
        stt_cost=Decimal("0.004000"),
        total_cost=Decimal("0.006500"),
    )

    db_session.add_all([user, room, transcript, ledger])
    await db_session.flush()

    stmt = select(Room).where(Room.id == room_id)
    fetched_room = (await db_session.execute(stmt)).scalar_one()
    assert fetched_room.title == "Quarterly Review 2026"
    assert len(fetched_room.transcripts) == 1
    assert len(fetched_room.usage_ledgers) == 1
    assert fetched_room.transcripts[0].summary_status == "READY"
