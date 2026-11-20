"""Unit tests for Wallet, PaymentTransaction, and Promo ORM models (app.models.wallet)."""

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.wallet import PaymentTransaction, PromoCode, PromoRedemption, Wallet


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
