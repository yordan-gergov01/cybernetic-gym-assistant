"""user_photos table

Revision ID: 0002_user_photos
Revises: 0001_initial
Create Date: 2026-07-20

Adds the user_photos table (progress / body-fat photos; the row stores only the R2
object key, not the image). The table already exists in some databases that were
created by hand before migrations, so the create is guarded by an existence check
to stay idempotent.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "0002_user_photos"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if "user_photos" in inspect(op.get_bind()).get_table_names():
        return  # already present (hand-created DB)
    op.create_table(
        "user_photos",
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("photo_type", sa.String(20), nullable=True),
        sa.Column("angle", sa.String(10), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("bf_pct_assessed", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("taken_at", sa.Date(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("user_photos")
