"""User and UserProfile SQLAlchemy 2.0 ORM Models.

Maps to PostgreSQL tables 'users' and 'user_profiles'.
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.room import Room
    from app.models.vocabulary import CustomVocabulary
    from app.models.wallet import PaymentTransaction, PromoRedemption, Wallet


class User(Base, TimestampMixin):
    """Core user record matching Cognito sub identifier."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="HOST", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)

    # Relationships
    profile: Mapped["UserProfile"] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    wallet: Mapped["Wallet"] = relationship(
        "Wallet",
        back_populates="host",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    rooms: Mapped[list["Room"]] = relationship(
        "Room",
        back_populates="host",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    vocabularies: Mapped[list["CustomVocabulary"]] = relationship(
        "CustomVocabulary",
        back_populates="host",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    payment_transactions: Mapped[list["PaymentTransaction"]] = relationship(
        "PaymentTransaction",
        back_populates="host",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    promo_redemptions: Mapped[list["PromoRedemption"]] = relationship(
        "PromoRedemption",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class UserProfile(Base, TimestampMixin):
    """Extended user metadata, default language preferences, and billing information."""

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Ho_Chi_Minh", nullable=False)
    default_source_lang: Mapped[str] = mapped_column(String(16), default="vi-VN", nullable=False)
    default_target_langs: Mapped[list[str]] = mapped_column(
        JSON,
        default=lambda: ["en-US"],
        nullable=False,
    )
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tax_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    company_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    preferences: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile", lazy="selectin")
