"""ratings on coaching answers

Revision ID: 0006_chat_message_rating
Revises: 0005_ai_interactions
Create Date: 2026-09-03

The traces added in 0005 say how an answer was built but not whether it was any good.
These columns hold the user's verdict on an assistant message, and the reason when they
give one, so weak answers can be found by query instead of by memory.

Nullable on purpose: an unrated answer is not a neutral one, it is one nobody judged, and
the two must not be summarised as the same thing.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_chat_message_rating"
down_revision: Union[str, None] = "0005_ai_interactions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chat_messages", sa.Column("rating", sa.Integer))
    op.add_column("chat_messages", sa.Column("rating_comment", sa.Text))
    op.add_column("chat_messages", sa.Column("rated_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("chat_messages", "rated_at")
    op.drop_column("chat_messages", "rating_comment")
    op.drop_column("chat_messages", "rating")
