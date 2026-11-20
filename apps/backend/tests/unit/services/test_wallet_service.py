"""Unit tests for WalletService (app.services.wallet_service)."""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    PaymentRequiredException,
    ValidationException,
)
from app.models.user import User
from app.models.wallet import PromoCode, Wallet
from app.repositories.wallet_repository import WalletRepository
from app.services.wallet_service import WalletService


async def test_wallet_service_top_up_and_deduct_usage(db_session: AsyncSession) -> None:
    wallet_repo = WalletRepository(session=db_session)
    service = WalletService(wallet_repo=wallet_repo)
    host_id = "test-host-wallet-srv-1"

    # Seed User & Wallet
    user = User(id=host_id, email="srv_wallet@example.com")
    wallet = Wallet(host_id=host_id, balance=Decimal("10.0000"))
    db_session.add_all([user, wallet])
    await db_session.flush()

    # 1. Top-up successfully
    updated_wallet = await service.top_up(
        host_id=host_id,
        amount=Decimal("20.0000"),
        provider="STRIPE",
        transaction_id="stripe_tx_101",
        metadata={"plan": "pro"},
    )
    assert updated_wallet.balance == Decimal("30.0000")

    # 2. Duplicate transaction raises ConflictException (Idempotency)
    with pytest.raises(ConflictException, match="already been processed"):
        await service.top_up(
            host_id=host_id,
            amount=Decimal("20.0000"),
            provider="STRIPE",
            transaction_id="stripe_tx_101",
        )

    # 3. Top-up non-positive amount raises ValidationException
    with pytest.raises(ValidationException, match="greater than 0"):
        await service.top_up(
            host_id=host_id,
            amount=Decimal("0.0000"),
            provider="STRIPE",
            transaction_id="stripe_tx_102",
        )

    # 4. Deduct 10s micro-billing usage
    post_deduct_wallet = await service.deduct_usage(
        host_id=host_id,
        cost=Decimal("0.0065"),
        room_id="room-test-1",
        interval_index=1,
    )
    assert post_deduct_wallet.balance == Decimal("29.9935")

    # 5. Overdraft attempt raises PaymentRequiredException
    with pytest.raises(PaymentRequiredException, match="Insufficient credits"):
        await service.deduct_usage(
            host_id=host_id,
            cost=Decimal("50.0000"),
            room_id="room-test-1",
            interval_index=2,
        )


async def test_wallet_service_promo_redemption(db_session: AsyncSession) -> None:
    wallet_repo = WalletRepository(session=db_session)
    service = WalletService(wallet_repo=wallet_repo)
    host_id = "test-host-wallet-srv-2"

    user = User(id=host_id, email="srv_promo@example.com")
    wallet = Wallet(host_id=host_id, balance=Decimal("0.0000"))
    promo = PromoCode(
        code="BONUS10",
        credit_amount=Decimal("10.0000"),
        max_redemptions=1,
        redemptions_count=0,
        is_active=True,
    )
    db_session.add_all([user, wallet, promo])
    await db_session.flush()

    # First redemption succeeds
    credit = await service.redeem_promo(host_id=host_id, code="bonus10")
    assert credit == Decimal("10.0000")

    wallet_check = await service.get_wallet(host_id)
    assert wallet_check.balance == Decimal("10.0000")

    # Second redemption exceeds limit
    with pytest.raises(ValidationException, match="maximum redemptions limit"):
        await service.redeem_promo(host_id=host_id, code="bonus10")

    # Non-existent promo raises NotFoundException
    with pytest.raises(NotFoundException, match="invalid or expired"):
        await service.redeem_promo(host_id=host_id, code="INVALID_CODE")


async def test_wallet_service_promo_duplicate_user_and_expiry_guards(
    db_session: AsyncSession,
) -> None:
    from datetime import UTC, datetime, timedelta

    wallet_repo = WalletRepository(session=db_session)
    service = WalletService(wallet_repo=wallet_repo)
    host_id = "test-host-wallet-srv-3"

    user = User(id=host_id, email="srv_promo_dup@example.com")
    wallet = Wallet(host_id=host_id, balance=Decimal("0.0000"))
    multi_promo = PromoCode(
        code="MULTI5",
        credit_amount=Decimal("5.0000"),
        max_redemptions=5,
        redemptions_count=0,
        is_active=True,
    )
    expired_promo = PromoCode(
        code="OLD5",
        credit_amount=Decimal("5.0000"),
        max_redemptions=5,
        redemptions_count=0,
        expires_at=datetime.now(UTC) - timedelta(minutes=5),
        is_active=True,
    )
    db_session.add_all([user, wallet, multi_promo, expired_promo])
    await db_session.flush()

    assert await service.redeem_promo(host_id=host_id, code="MULTI5") == Decimal("5.0000")

    # Same user redeeming MULTI5 again fails with ConflictException and rolls back counter
    with pytest.raises(ConflictException, match="already been redeemed"):
        await service.redeem_promo(host_id=host_id, code="MULTI5")

    refreshed_promo = await wallet_repo.get_promo_code_by_code("MULTI5")
    assert refreshed_promo is not None
    assert refreshed_promo.redemptions_count == 1

    # Expired promo raises NotFoundException
    with pytest.raises(NotFoundException, match="invalid or expired"):
        await service.redeem_promo(host_id=host_id, code="OLD5")
