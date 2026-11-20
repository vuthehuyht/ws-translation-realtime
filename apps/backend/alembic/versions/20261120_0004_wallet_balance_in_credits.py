"""Denominate wallet amounts in Credits and drop the currency columns.

Revision ID: 0004_wallet_balance_in_credits
Revises: 0003_add_deleted_account_records
Create Date: 2026-11-20 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_wallet_balance_in_credits"
down_revision: str | None = "0003_add_deleted_account_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixed conversion rate: 1 USD = 100 Credits.
CREDITS_PER_USD = 100

# (table, column) pairs that held USD amounts and must be converted to Credits.
_AMOUNT_COLUMNS = (
    ("wallets", "balance"),
    ("wallets", "auto_topup_threshold"),
    ("wallets", "auto_topup_amount"),
    ("payment_transactions", "amount"),
    ("promo_codes", "credit_amount"),
    ("promo_redemptions", "credit_amount"),
)


def upgrade() -> None:
    for table, column in _AMOUNT_COLUMNS:
        op.execute(f"UPDATE {table} SET {column} = {column} * {CREDITS_PER_USD}")  # noqa: S608

    op.drop_column("wallets", "currency")
    op.drop_column("payment_transactions", "currency")


def downgrade() -> None:
    op.add_column(
        "payment_transactions",
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
    )
    op.add_column(
        "wallets",
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
    )

    for table, column in _AMOUNT_COLUMNS:
        op.execute(f"UPDATE {table} SET {column} = {column} / {CREDITS_PER_USD}")  # noqa: S608
