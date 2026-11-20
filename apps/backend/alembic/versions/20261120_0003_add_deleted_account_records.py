"""Add deleted_account_records table for GDPR deletion cooldown and bonus eligibility.

Revision ID: 0003_add_deleted_account_records
Revises: 0002_add_profile_phone_bio
Create Date: 2026-11-20 19:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_add_deleted_account_records"
down_revision: str | None = "0002_add_profile_phone_bio"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "deleted_account_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email_hash", sa.String(length=64), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("re_register_allowed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deletion_count", sa.Integer(), server_default="1", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_deleted_account_records_email_hash",
        "deleted_account_records",
        ["email_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_deleted_account_records_email_hash", table_name="deleted_account_records")
    op.drop_table("deleted_account_records")
