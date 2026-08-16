"""password reset tokens

Revision ID: 0004_password_reset
Revises: 0003_intake_fields
Create Date: 2026-08-15

A forgotten password used to mean a dead account: the app had register and login and
nothing else. This table holds the one-time keys emailed out by /auth/forgot-password.

Only the hash of a token is stored, so the table cannot be used to enter the accounts it
belongs to, and used rows are kept rather than deleted so a link cannot be replayed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_password_reset"
down_revision: Union[str, None] = "0003_intake_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
