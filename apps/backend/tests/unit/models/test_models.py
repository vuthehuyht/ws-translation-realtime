"""Unit tests for Database Models, Relationships, and Constraints (app.models)."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room, RoomTranscript, UsageLedger
from app.models.user import User, UserProfile
from app.models.vocabulary import CustomVocabulary
from app.models.wallet import PaymentTransaction, PromoCode, PromoRedemption, Wallet


async def test_create_user_and_profile_relationship(db_session: AsyncSession) -> None:
    user_id = "test-cognito-sub-12345"
    user = User(
        id=user_id,
        email="host@example.com",
        role="HOST",
        status="ACTIVE",
    )
    profile = UserProfile(
        user_id=user_id,
        full_name="Nguyễn Văn A",
        default_source_lang="vi-VN",
        default_target_langs=["en-US", "ja-JP"],
        timezone="Asia/Ho_Chi_Minh",
    )
    db_session.add(user)
    db_session.add(profile)
    await db_session.flush()

    # Query back
    stmt = select(User).where(User.id == user_id)
    result = await db_session.execute(stmt)
    fetched_user = result.scalar_one()

    assert fetched_user.email == "host@example.com"
    assert fetched_user.profile is not None
    assert fetched_user.profile.full_name == "Nguyễn Văn A"
    assert fetched_user.profile.default_target_langs == ["en-US", "ja-JP"]


async def test_duplicate_email_violates_unique_constraint(db_session: AsyncSession) -> None:
    user1 = User(id="sub-1", email="duplicate@example.com")
    user2 = User(id="sub-2", email="duplicate@example.com")
    db_session.add(user1)
    await db_session.flush()

    db_session.add(user2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


async def test_wallet_and_payment_transactions(db_session: AsyncSession) -> None:
    user_id = "host-wallet-test-sub"
    user = User(id=user_id, email="wallet_host@example.com")
    wallet = Wallet(
        host_id=user_id,
        balance=Decimal("25.5000"),
        auto_degrade_tts=True,
        auto_topup_enabled=False,
    )
    tx = PaymentTransaction(
        host_id=user_id,
        transaction_id="stripe_pi_test_123",
        type="TOP_UP",
        provider="STRIPE",
        amount=Decimal("20.0000"),
        currency="USD",
        status="SUCCEEDED",
        metadata_json={"brand": "Visa", "last4": "4242"},
    )
    db_session.add_all([user, wallet, tx])
    await db_session.flush()

    stmt = select(Wallet).where(Wallet.host_id == user_id)
    fetched_wallet = (await db_session.execute(stmt)).scalar_one()
    assert fetched_wallet.balance == Decimal("25.5000")
    assert fetched_wallet.auto_degrade_tts is True

    tx_stmt = select(PaymentTransaction).where(PaymentTransaction.host_id == user_id)
    fetched_tx = (await db_session.execute(tx_stmt)).scalar_one()
    assert fetched_tx.transaction_id == "stripe_pi_test_123"
    assert fetched_tx.amount == Decimal("20.0000")


async def test_promo_codes_and_redemptions(db_session: AsyncSession) -> None:
    user_id = "promo-test-sub"
    user = User(id=user_id, email="promo_user@example.com")
    promo = PromoCode(
        code="WELCOME2026",
        credit_amount=Decimal("5.0000"),
        max_redemptions=100,
        redemptions_count=0,
    )
    db_session.add_all([user, promo])
    await db_session.flush()

    redemption = PromoRedemption(
        promo_code_id=promo.id,
        user_id=user_id,
        credit_amount=promo.credit_amount,
    )
    db_session.add(redemption)
    await db_session.flush()

    # Second redemption by the same user should fail unique constraint
    duplicate_redemption = PromoRedemption(
        promo_code_id=promo.id,
        user_id=user_id,
        credit_amount=promo.credit_amount,
    )
    db_session.add(duplicate_redemption)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


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
    vocab = CustomVocabulary(
        host_id=user_id,
        name="Medical Terms",
        language_code="vi-VN",
        terms=["Huyết áp", "Kháng sinh"],
    )

    db_session.add_all([user, room, transcript, ledger, vocab])
    await db_session.flush()

    stmt = select(Room).where(Room.id == room_id)
    fetched_room = (await db_session.execute(stmt)).scalar_one()
    assert fetched_room.title == "Quarterly Review 2026"
    assert len(fetched_room.transcripts) == 1
    assert len(fetched_room.usage_ledgers) == 1
    assert fetched_room.transcripts[0].summary_status == "READY"
