"""ai interaction traces

Revision ID: 0005_ai_interactions
Revises: 0004_password_reset
Create Date: 2026-09-03

Nothing recorded what the coach was told before it answered. This table holds one row
per model call: the question, the query retrieval actually ran, the course passages that
came back (as chunk ids and scores, not as text), the prompt version that was live, and
the latency and token counts of the call.

Indexed on user and time because both readings start there - one user's history when an
answer looks wrong, and the last N calls when latency or cost moves.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_ai_interactions"
down_revision: Union[str, None] = "0004_password_reset"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_interactions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("surface", sa.String(30), nullable=False),
        sa.Column(
            "message_id",
            sa.dialects.postgresql.UUID(as_uuid=False),
            sa.ForeignKey("chat_messages.id"),
        ),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("resolved_query", sa.Text),
        sa.Column("retrieved", sa.dialects.postgresql.JSONB),
        sa.Column("prompt_name", sa.String(50)),
        sa.Column("prompt_version", sa.String(10)),
        sa.Column("model", sa.String(60)),
        sa.Column("temperature", sa.Float),
        sa.Column("input_tokens", sa.Integer),
        sa.Column("output_tokens", sa.Integer),
        sa.Column("retrieval_ms", sa.Integer),
        sa.Column("generation_ms", sa.Integer),
        sa.Column("total_ms", sa.Integer),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_interactions_user_id", "ai_interactions", ["user_id"])
    op.create_index("ix_ai_interactions_created_at", "ai_interactions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_interactions_created_at", table_name="ai_interactions")
    op.drop_index("ix_ai_interactions_user_id", table_name="ai_interactions")
    op.drop_table("ai_interactions")
