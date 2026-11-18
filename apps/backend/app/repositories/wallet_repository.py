"""Wallet and PaymentTransaction Async Repository.

Provides data access methods for Wallet balance, Transactions, and Promo Codes.
"""

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import or_, select, update
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

        Enforces non-negative balance in the SQL WHERE predicate so concurrent deductions
        cannot race past a read-before-write check.
        """
        stmt = update(Wallet).where(Wallet.host_id == host_id)
        if not allow_negative and amount_delta < Decimal("0.0000"):
            stmt = stmt.where(Wallet.balance + amount_delta >= Decimal("0.0000"))

        stmt = stmt.values(balance=Wallet.balance + amount_delta).returning(Wallet)
        result = await self.session.execute(stmt)
        updated_wallet = result.scalar_one_or_none()
        if updated_wallet is not None:
            await self.session.flush()
            return updated_wallet

        # Distinguish missing wallet from insufficient balance only when UPDATE matched 0 rows.
        wallet = await self.get_by_host_id(host_id)
        if not wallet:
            raise NotFoundException("Host wallet not found")

        required = abs(amount_delta)
        raise PaymentRequiredException(
            f"Insufficient funds: Current balance is ${wallet.balance}, required ${required}"
        )

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

    async def get_promo_code_by_code(
        self, code: str, *, active_only: bool = True
    ) -> PromoCode | None:
        """Look up a promo code by its normalized code identifier."""
        stmt = select(PromoCode).where(PromoCode.code == code.strip().upper())
        if active_only:
            stmt = stmt.where(PromoCode.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def claim_promo_code_atomic(self, code: str, now: datetime) -> PromoCode | None:
        """Atomically increment promo redemptions_count only while quota and expiry allow."""
        normalized_code = code.strip().upper()
        stmt = (
            update(PromoCode)
            .where(
                PromoCode.code == normalized_code,
                PromoCode.is_active.is_(True),
                PromoCode.redemptions_count < PromoCode.max_redemptions,
                or_(PromoCode.expires_at.is_(None), PromoCode.expires_at > now),
            )
            .values(redemptions_count=PromoCode.redemptions_count + 1)
            .returning(PromoCode)
        )
        result = await self.session.execute(stmt)
        claimed = result.scalar_one_or_none()
        if claimed is not None:
            await self.session.flush()
        return claimed

    async def record_promo_redemption(self, redemption: PromoRedemption) -> PromoRedemption:
        """Record promo code redemption."""
        self.session.add(redemption)
        await self.session.flush()
        await self.session.refresh(redemption)
        return redemption
