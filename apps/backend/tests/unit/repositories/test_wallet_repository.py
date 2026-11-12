"""Unit tests for WalletRepository (app.repositories.wallet_repository)."""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, PaymentRequiredException
from app.models.user import User
from app.models.wallet import PaymentTransaction, PromoCode, PromoRedemption, Wallet
from app.repositories.wallet_repository import WalletRepository


async def test_wallet_repository_balance_atomic_updates(db_session: AsyncSession) -> None:
    repo = WalletRepository(session=db_session)
    host_id = "wallet-host-101"

    # Seed User & Wallet
    user = User(id=host_id, email="wallet101@example.com")
    wallet = Wallet(host_id=host_id, balance=Decimal("10.0000"))
    db_session.add_all([user, wallet])
    await db_session.flush()

    # Credit (Deposit)
    updated = await repo.update_balance_atomic(host_id=host_id, amount_delta=Decimal("5.5000"))
    assert updated.balance == Decimal("15.5000")

    # Debit (Usage)
    updated = await repo.update_balance_atomic(host_id=host_id, amount_delta=Decimal("-3.2500"))
    assert updated.balance == Decimal("12.2500")

    # Overdraft rejected when allow_negative=False
    with pytest.raises(PaymentRequiredException, match="Insufficient funds"):
        await repo.update_balance_atomic(host_id=host_id, amount_delta=Decimal("-20.0000"))

    # Non-existent host raises NotFoundException
    with pytest.raises(NotFoundException):
        await repo.update_balance_atomic(host_id="unknown-host", amount_delta=Decimal("1.0000"))


async def test_wallet_repository_transactions_and_promo(db_session: AsyncSession) -> None:
    repo = WalletRepository(session=db_session)
    host_id = "wallet-host-102"

    user = User(id=host_id, email="wallet102@example.com")
    wallet = Wallet(host_id=host_id, balance=Decimal("0.0000"))
    db_session.add_all([user, wallet])
    await db_session.flush()

    # 1. Create Transaction
    tx = PaymentTransaction(
        host_id=host_id,
        transaction_id="stripe_ch_9999",
        type="TOP_UP",
        provider="STRIPE",
        amount=Decimal("50.0000"),
        currency="USD",
        status="SUCCEEDED",
    )
    saved_tx = await repo.create_transaction(tx)
    assert saved_tx.id is not None

    # Fetch by provider ID
    fetched_tx = await repo.get_transaction_by_provider_id("stripe_ch_9999")
    assert fetched_tx is not None
    assert fetched_tx.amount == Decimal("50.0000")

    # List transactions
    tx_list = await repo.list_transactions(host_id=host_id)
    assert len(tx_list) == 1

    # 2. Promo Code lookup and redemption
    promo = PromoCode(
        code="PROMO50",
        credit_amount=Decimal("5.0000"),
        max_redemptions=10,
        redemptions_count=0,
        is_active=True,
    )
    db_session.add(promo)
    await db_session.flush()

    found_promo = await repo.get_promo_code_by_code("promo50")
    assert found_promo is not None
    assert found_promo.code == "PROMO50"

    redemption = PromoRedemption(
        promo_code_id=found_promo.id,
        user_id=host_id,
        credit_amount=found_promo.credit_amount,
    )
    recorded_redemption = await repo.record_promo_redemption(redemption)
    assert recorded_redemption.id is not None
