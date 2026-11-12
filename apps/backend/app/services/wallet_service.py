"""Wallet and Billing Business Service.

Handles host balance queries, payment top-ups, and 10-second micro-billing deductions.
"""

from decimal import Decimal
from typing import Any

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models.wallet import PaymentTransaction, PromoRedemption, Wallet
from app.repositories.wallet_repository import WalletRepository


class WalletService:
    """Service encapsulating balance management, top-ups, and micro-billing deductions."""

    def __init__(self, wallet_repo: WalletRepository) -> None:
        self.wallet_repo = wallet_repo

    async def get_wallet(self, host_id: str) -> Wallet:
        """Fetch host wallet or raise NotFoundException."""
        wallet = await self.wallet_repo.get_by_host_id(host_id)
        if not wallet:
            raise NotFoundException(f"Wallet for host '{host_id}' not found")
        return wallet

    async def top_up(
        self,
        host_id: str,
        amount: Decimal,
        provider: str,
        transaction_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Wallet:
        """Credit host wallet atomically from Stripe or VietQR payment webhook."""
        if amount <= Decimal("0.0000"):
            raise ValidationException("Top-up amount must be strictly greater than 0")

        # Idempotency check: prevent double-crediting
        existing_tx = await self.wallet_repo.get_transaction_by_provider_id(transaction_id)
        if existing_tx:
            raise ConflictException(f"Transaction '{transaction_id}' has already been processed")

        # Atomically credit wallet
        wallet = await self.wallet_repo.update_balance_atomic(
            host_id=host_id,
            amount_delta=amount,
            allow_negative=False,
        )

        # Record payment transaction
        tx = PaymentTransaction(
            host_id=host_id,
            transaction_id=transaction_id,
            type="TOP_UP",
            provider=provider,
            amount=amount,
            currency="USD",
            status="SUCCEEDED",
            metadata_json=metadata or {},
        )
        await self.wallet_repo.create_transaction(tx)

        return wallet

    async def deduct_usage(
        self,
        host_id: str,
        cost: Decimal,
        room_id: str,
        interval_index: int,
    ) -> Wallet:
        """Atomically deduct 10-second micro-billing interval cost from host wallet."""
        if cost < Decimal("0.0000"):
            raise ValidationException("Usage cost cannot be negative")

        if cost == Decimal("0.0000"):
            return await self.get_wallet(host_id)

        # Atomically deduct cost
        wallet = await self.wallet_repo.update_balance_atomic(
            host_id=host_id,
            amount_delta=-cost,
            allow_negative=False,
        )

        # Record micro-billing deduction transaction
        tx_id = f"micro_{room_id}_{interval_index}"
        tx = PaymentTransaction(
            host_id=host_id,
            transaction_id=tx_id,
            type="USAGE_DEDUCTION",
            provider="INTERNAL",
            amount=-cost,
            currency="USD",
            status="SUCCEEDED",
            metadata_json={"roomId": room_id, "intervalIndex": interval_index},
        )
        await self.wallet_repo.create_transaction(tx)

        return wallet

    async def redeem_promo(self, host_id: str, code: str) -> Decimal:
        """Redeem a promotional credit code into the host wallet."""
        promo = await self.wallet_repo.get_promo_code_by_code(code)
        if not promo or not promo.is_active:
            raise NotFoundException(f"Promo code '{code}' is invalid or expired")

        if promo.redemptions_count >= promo.max_redemptions:
            raise ValidationException(
                f"Promo code '{code}' has reached its maximum redemptions limit"
            )

        # Credit wallet
        await self.wallet_repo.update_balance_atomic(
            host_id=host_id,
            amount_delta=promo.credit_amount,
            allow_negative=False,
        )

        # Record redemption
        redemption = PromoRedemption(
            promo_code_id=promo.id,
            user_id=host_id,
            credit_amount=promo.credit_amount,
        )
        await self.wallet_repo.record_promo_redemption(redemption)

        # Increment redemptions counter
        promo.redemptions_count += 1
        await self.wallet_repo.session.flush()

        return promo.credit_amount
