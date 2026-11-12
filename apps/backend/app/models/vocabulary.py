"""CustomVocabulary SQLAlchemy 2.0 ORM Model.

Maps to PostgreSQL table 'custom_vocabularies'.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class CustomVocabulary(Base, TimestampMixin):
    """Domain-specific terminology dictionary synced with Amazon Transcribe."""

    __tablename__ = "custom_vocabularies"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    host_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    language_code: Mapped[str] = mapped_column(String(16), default="vi-VN", nullable=False)
    terms: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    aws_vocab_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)

    # Relationships
    host: Mapped["User"] = relationship("User", back_populates="vocabularies", lazy="selectin")
