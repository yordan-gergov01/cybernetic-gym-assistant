"""a trace is deleted with the message it explains

Revision ID: 0007_trace_cascade
Revises: 0006_chat_message_rating
Create Date: 2026-09-17

Clearing the chat history failed: ai_interactions.message_id pointed at chat_messages
with no delete behaviour, so Postgres refused to remove a message a trace referenced.

The rule is not only technical. A trace stores the question verbatim, and the screen
tells the user their conversation will be deleted; a row that outlives it would keep
that conversation in a second table. So the trace goes with the message it explains.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0007_trace_cascade"
down_revision: Union[str, None] = "0006_chat_message_rating"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ai_interactions_message_id_fkey", "ai_interactions", type_="foreignkey")
    op.create_foreign_key(
        "ai_interactions_message_id_fkey",
        "ai_interactions",
        "chat_messages",
        ["message_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("ai_interactions_message_id_fkey", "ai_interactions", type_="foreignkey")
    op.create_foreign_key(
        "ai_interactions_message_id_fkey",
        "ai_interactions",
        "chat_messages",
        ["message_id"],
        ["id"],
    )
