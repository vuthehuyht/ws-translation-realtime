"""Unit tests for RoomRepository (app.repositories.room_repository)."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room, RoomTranscript, UsageLedger
from app.models.user import User
from app.repositories.room_repository import RoomRepository


async def test_room_repository_lifecycle_and_ledger(db_session: AsyncSession) -> None:
    repo = RoomRepository(session=db_session)
    host_id = "room-host-201"
    room_id = "room-session-201"

    # Seed User
    user = User(id=host_id, email="room201@example.com")
    db_session.add(user)
    await db_session.flush()

    # Create Room
    room = Room(
        id=room_id,
        host_id=host_id,
        title="Engineering Standup",
        source_language="en-US",
        target_languages=["vi-VN", "ja-JP"],
        status="ACTIVE",
        host_token_hash="token_hash_abc",
        started_at=datetime.now(UTC),
    )
    created_room = await repo.create(room)
    assert created_room.id == room_id
    assert created_room.status == "ACTIVE"

    # List by host
    host_rooms = await repo.list_by_host(host_id=host_id)
    assert len(host_rooms) == 1
    assert host_rooms[0].title == "Engineering Standup"

    # Update status to CLOSED
    now = datetime.now(UTC)
    updated = await repo.update_status(room_id=room_id, status="CLOSED", ended_at=now)
    assert updated is not None
    assert updated.status == "CLOSED"
    assert updated.ended_at is not None

    # Record Transcript
    transcript = RoomTranscript(
        room_id=room_id,
        s3_key_master=f"transcripts/{room_id}/master.json",
        summary_status="PENDING",
    )
    saved_transcript = await repo.save_transcript(transcript)
    assert saved_transcript.room_id == room_id

    # Fetch transcript
    fetched_transcript = await repo.get_transcript_by_room_id(room_id)
    assert fetched_transcript is not None
    assert fetched_transcript.summary_status == "PENDING"

    # Record Usage Ledger
    ledger = UsageLedger(
        room_id=room_id,
        interval_index=1,
        start_time=now,
        end_time=now,
        audio_seconds=Decimal("10.00"),
        stt_cost=Decimal("0.004000"),
        total_cost=Decimal("0.004000"),
    )
    saved_ledger = await repo.record_usage_ledger(ledger)
    assert saved_ledger.interval_index == 1

    # List ledgers
    ledgers = await repo.list_usage_ledgers(room_id)
    assert len(ledgers) == 1
    assert ledgers[0].total_cost == Decimal("0.004000")
