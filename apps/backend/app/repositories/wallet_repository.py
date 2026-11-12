"""Wallet and PaymentTransaction Async Repository.

Provides data access methods for Wallet balance, Transactions, and Promo Codes.
"""

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, PaymentRequiredException
from app.models.wallet import PaymentTransaction, PromoCode, PromoRedemption, Wallet
from app.repositories.base import BaseRepository


class WalletRepository(BaseRepository[Wallet]):
    """Repository handling Wallet, Transaction, and Promo Code database queries."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model_cls=Wallet)

    async def get_by_host_id(self, host_id: str) -> Wallet | None:
        """Fetch host wallet record by host user ID."""
        stmt = select(Wallet).where(Wallet.host_id == host_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_balance_atomic(
        self,
        host_id: str,
        amount_delta: Decimal,
        allow_negative: bool = False,
    ) -> Wallet:
        """Atomically increment/decrement wallet balance in a single SQL operation.

        Args:
            host_id: Target user ID
            amount_delta: Amount to add (positive) or deduct (negative)
            allow_negative: Whether the balance is permitted to drop below zero

        Raises:
            NotFoundException: If the host wallet does not exist
            PaymentRequiredException: If decrement would cause negative balance and not allowed
        """
        wallet = await self.get_by_host_id(host_id)
        if not wallet:
            raise NotFoundException(f"Wallet for host '{host_id}' not found")

        is_overdraft = (wallet.balance + amount_delta) < Decimal("0.0000")
        if not allow_negative and amount_delta < 0 and is_overdraft:
            required = abs(amount_delta)
            raise PaymentRequiredException(
                f"Insufficient funds: Current balance is ${wallet.balance}, required ${required}"
            )

        stmt = (
            update(Wallet)
            .where(Wallet.host_id == host_id)
            .values(balance=Wallet.balance + amount_delta)
            .returning(Wallet)
        )
        result = await self.session.execute(stmt)
        updated_wallet = result.scalar_one()
        await self.session.flush()
        return updated_wallet

    async def create_transaction(self, tx: PaymentTransaction) -> PaymentTransaction:
        """Persist a payment or micro-billing transaction record."""
        self.session.add(tx)
        await self.session.flush()
        await self.session.refresh(tx)
        return tx

    async def get_transaction_by_provider_id(
        self,
        transaction_id: str,
    ) -> PaymentTransaction | None:
        """Find an external payment transaction by provider transaction reference ID."""
        stmt = select(PaymentTransaction).where(PaymentTransaction.transaction_id == transaction_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_transactions(
        self,
        host_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[PaymentTransaction]:
        """Fetch paginated transaction history for a host."""
        stmt = (
            select(PaymentTransaction)
            .where(PaymentTransaction.host_id == host_id)
            .order_by(PaymentTransaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_promo_code_by_code(self, code: str) -> PromoCode | None:
        """Look up an active promo code by its code identifier."""
        stmt = select(PromoCode).where(
            PromoCode.code == code.strip().upper(),
            PromoCode.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def record_promo_redemption(self, redemption: PromoRedemption) -> PromoRedemption:
        """Record promo code redemption."""
        self.session.add(redemption)
        await self.session.flush()
        await self.session.refresh(redemption)
        return redemption
