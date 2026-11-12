"""Wallet, Payment Transactions, and Promo Codes SQLAlchemy 2.0 ORM Models.

Maps to PostgreSQL tables 'wallets', 'payment_transactions', 'promo_codes',
and 'promo_redemptions'.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Wallet(Base, TimestampMixin):
    """Host prepaid balance wallet with auto-degrade and auto top-up settings."""

    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    host_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    auto_degrade_tts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_topup_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_topup_threshold: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    auto_topup_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    default_payment_method_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Relationships
    host: Mapped["User"] = relationship("User", back_populates="wallet", lazy="selectin")


class PaymentTransaction(Base):
    """Financial ledger transactions (Top-up, Auto Top-up, Promo Credit, Session Usage)."""

    __tablename__ = "payment_transactions"

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
    transaction_id: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        index=True,
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    host: Mapped["User"] = relationship(
        "User", back_populates="payment_transactions", lazy="selectin"
    )


class PromoCode(Base):
    """Promotional discount codes for wallet credits."""

    __tablename__ = "promo_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    max_redemptions: Mapped[int] = mapped_column(Integer, nullable=False)
    redemptions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    redemptions: Mapped[list["PromoRedemption"]] = relationship(
        "PromoRedemption",
        back_populates="promo_code",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class PromoRedemption(Base):
    """History of promo code redemptions per user to prevent duplicate usage."""

    __tablename__ = "promo_redemptions"
    __table_args__ = (UniqueConstraint("promo_code_id", "user_id", name="uq_promo_code_user"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    promo_code_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("promo_codes.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    redeemed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    promo_code: Mapped["PromoCode"] = relationship(
        "PromoCode", back_populates="redemptions", lazy="selectin"
    )
    user: Mapped["User"] = relationship("User", back_populates="promo_redemptions", lazy="selectin")
