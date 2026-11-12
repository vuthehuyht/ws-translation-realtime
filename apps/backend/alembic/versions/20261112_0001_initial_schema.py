"""Initial PostgreSQL 16 schema with 9 tables.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-12 22:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="HOST"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # 2. user_profiles
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=1024), nullable=True),
        sa.Column(
            "timezone", sa.String(length=64), nullable=False, server_default="Asia/Ho_Chi_Minh"
        ),
        sa.Column(
            "default_source_lang", sa.String(length=16), nullable=False, server_default="vi-VN"
        ),
        sa.Column("default_target_langs", sa.JSON(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("tax_code", sa.String(length=64), nullable=True),
        sa.Column("company_address", sa.String(length=512), nullable=True),
        sa.Column("stripe_customer_id", sa.String(length=128), nullable=True),
        sa.Column("preferences", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_profiles_user_id"), "user_profiles", ["user_id"], unique=True)
    op.create_index(
        op.f("ix_user_profiles_stripe_customer_id"),
        "user_profiles",
        ["stripe_customer_id"],
        unique=False,
    )

    # 3. wallets
    op.create_table(
        "wallets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("host_id", sa.String(length=64), nullable=False),
        sa.Column(
            "balance", sa.Numeric(precision=12, scale=4), nullable=False, server_default="0.0000"
        ),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column("auto_degrade_tts", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("auto_topup_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("auto_topup_threshold", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("auto_topup_amount", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("default_payment_method_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["host_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_wallets_host_id"), "wallets", ["host_id"], unique=True)

    # 4. payment_transactions
    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("host_id", sa.String(length=64), nullable=False),
        sa.Column("transaction_id", sa.String(length=128), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["host_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_payment_transactions_host_id"), "payment_transactions", ["host_id"], unique=False
    )
    op.create_index(
        op.f("ix_payment_transactions_transaction_id"),
        "payment_transactions",
        ["transaction_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_payment_transactions_type"), "payment_transactions", ["type"], unique=False
    )
    op.create_index(
        op.f("ix_payment_transactions_status"), "payment_transactions", ["status"], unique=False
    )

    # 5. promo_codes
    op.create_table(
        "promo_codes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("credit_amount", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("max_redemptions", sa.Integer(), nullable=False),
        sa.Column("redemptions_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_promo_codes_code"), "promo_codes", ["code"], unique=True)

    # 6. promo_redemptions
    op.create_table(
        "promo_redemptions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("promo_code_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("credit_amount", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["promo_code_id"], ["promo_codes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("promo_code_id", "user_id", name="uq_promo_code_user"),
    )
    op.create_index(
        op.f("ix_promo_redemptions_user_id"), "promo_redemptions", ["user_id"], unique=False
    )

    # 7. custom_vocabularies
    op.create_table(
        "custom_vocabularies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("host_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("language_code", sa.String(length=16), nullable=False),
        sa.Column("terms", sa.JSON(), nullable=False),
        sa.Column("aws_vocab_name", sa.String(length=128), nullable=True),
        sa.Column("sync_status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["host_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_custom_vocabularies_host_id"), "custom_vocabularies", ["host_id"], unique=False
    )

    # 8. rooms
    op.create_table(
        "rooms",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("host_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_language", sa.String(length=16), nullable=False),
        sa.Column("target_languages", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="IDLE"),
        sa.Column("host_token_hash", sa.String(length=128), nullable=False),
        sa.Column("listener_passcode", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["host_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rooms_id"), "rooms", ["id"], unique=False)
    op.create_index(op.f("ix_rooms_host_id"), "rooms", ["host_id"], unique=False)
    op.create_index(op.f("ix_rooms_status"), "rooms", ["status"], unique=False)

    # 9. room_transcripts
    op.create_table(
        "room_transcripts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.String(length=64), nullable=False),
        sa.Column("s3_key_master", sa.String(length=512), nullable=True),
        sa.Column("s3_key_txt", sa.String(length=512), nullable=True),
        sa.Column("s3_key_srt", sa.String(length=512), nullable=True),
        sa.Column("s3_key_vtt", sa.String(length=512), nullable=True),
        sa.Column("s3_key_csv", sa.String(length=512), nullable=True),
        sa.Column("summary_status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("summary_s3_key", sa.String(length=512), nullable=True),
        sa.Column(
            "summary_cost_usd",
            sa.Numeric(precision=8, scale=4),
            nullable=False,
            server_default="0.0000",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_room_transcripts_room_id"), "room_transcripts", ["room_id"], unique=False
    )

    # 10. usage_ledger
    op.create_table(
        "usage_ledger",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.String(length=64), nullable=False),
        sa.Column("interval_index", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("audio_seconds", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column(
            "stt_cost", sa.Numeric(precision=10, scale=6), nullable=False, server_default="0.000000"
        ),
        sa.Column("mt_character_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "mt_cost", sa.Numeric(precision=10, scale=6), nullable=False, server_default="0.000000"
        ),
        sa.Column("tts_character_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "tts_cost", sa.Numeric(precision=10, scale=6), nullable=False, server_default="0.000000"
        ),
        sa.Column("fanout_event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "fanout_cost",
            sa.Numeric(precision=10, scale=6),
            nullable=False,
            server_default="0.000000",
        ),
        sa.Column("total_cost", sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_usage_ledger_room_id"), "usage_ledger", ["room_id"], unique=False)


def downgrade() -> None:
    op.drop_table("usage_ledger")
    op.drop_table("room_transcripts")
    op.drop_table("rooms")
    op.drop_table("custom_vocabularies")
    op.drop_table("promo_redemptions")
    op.drop_table("promo_codes")
    op.drop_table("payment_transactions")
    op.drop_table("wallets")
    op.drop_table("user_profiles")
    op.drop_table("users")
