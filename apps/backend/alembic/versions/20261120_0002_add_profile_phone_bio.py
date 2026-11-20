"""Add phone_number and bio columns to user_profiles.

Revision ID: 0002_add_profile_phone_bio
Revises: 0001_initial_schema
Create Date: 2026-11-20 07:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_add_profile_phone_bio"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column("phone_number", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "user_profiles",
        sa.Column("bio", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_profiles", "bio")
    op.drop_column("user_profiles", "phone_number")
