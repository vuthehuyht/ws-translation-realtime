"""Room, RoomTranscript, and UsageLedger SQLAlchemy 2.0 ORM Models.

Maps to PostgreSQL tables 'rooms', 'room_transcripts', and 'usage_ledger'.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Room(Base, TimestampMixin):
    """Realtime speech translation meeting room."""

    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    host_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_language: Mapped[str] = mapped_column(String(16), default="vi-VN", nullable=False)
    target_languages: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="IDLE", index=True, nullable=False)
    host_token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    listener_passcode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    host: Mapped["User"] = relationship("User", back_populates="rooms", lazy="selectin")
    transcripts: Mapped[list["RoomTranscript"]] = relationship(
        "RoomTranscript",
        back_populates="room",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    usage_ledgers: Mapped[list["UsageLedger"]] = relationship(
        "UsageLedger",
        back_populates="room",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class RoomTranscript(Base, TimestampMixin):
    """Permanent S3 export packages and AI meeting summary metadata."""

    __tablename__ = "room_transcripts"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    room_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    s3_key_master: Mapped[str | None] = mapped_column(String(512), nullable=True)
    s3_key_txt: Mapped[str | None] = mapped_column(String(512), nullable=True)
    s3_key_srt: Mapped[str | None] = mapped_column(String(512), nullable=True)
    s3_key_vtt: Mapped[str | None] = mapped_column(String(512), nullable=True)
    s3_key_csv: Mapped[str | None] = mapped_column(String(512), nullable=True)
    summary_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    summary_s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    summary_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(8, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )

    # Relationships
    room: Mapped["Room"] = relationship("Room", back_populates="transcripts", lazy="selectin")


class UsageLedger(Base):
    """10-second micro-billing cost breakdown audit ledger."""

    __tablename__ = "usage_ledger"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    room_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    interval_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    audio_seconds: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    stt_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), default=Decimal("0.000000"), nullable=False
    )
    mt_character_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mt_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), default=Decimal("0.000000"), nullable=False
    )
    tts_character_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tts_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), default=Decimal("0.000000"), nullable=False
    )
    fanout_event_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fanout_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), default=Decimal("0.000000"), nullable=False
    )
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    room: Mapped["Room"] = relationship("Room", back_populates="usage_ledgers", lazy="selectin")
