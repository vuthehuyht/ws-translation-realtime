"""Base Declarative Model and Timestamp Mixins.

Provides the DeclarativeBase for SQLAlchemy 2.0 with type annotations
and standardized UTC timestamp mixins for all relational tables.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Root DeclarativeBase for all SQLAlchemy 2.0 ORM models."""

    pass


class TimestampMixin:
    """Standardized UTC created_at and updated_at datetime mixin."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
