"""coaching intake fields on user_profiles

Revision ID: 0003_intake_fields
Revises: 0002_user_photos
Create Date: 2026-07-30

Adds the fields from the Henselmans PT client intake form that actually change a
coaching decision: available load increments, recovery inputs (stress, sleep),
dedication level, scheduling constraints, detailed equipment, and current program/diet.
All are nullable so existing profiles stay valid.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_intake_fields"
down_revision: Union[str, None] = "0002_user_photos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLUMNS = [
    ("min_barbell_increment_kg", sa.Float()),
    ("min_dumbbell_increment_kg", sa.Float()),
    ("stress_level", sa.String(20)),
    ("sleep_quality", sa.String(10)),
    ("sleep_hours", sa.Float()),
    ("dedication_level", sa.String(20)),
    ("unavailable_times", sa.Text()),
    ("equipment_details", postgresql.JSONB()),
    ("avoid_growth_muscles", postgresql.JSONB()),
    ("other_activities", sa.Text()),
    ("occupation", sa.String(120)),
    ("caffeine_mg_per_day", sa.Integer()),
    ("current_program", sa.Text()),
    ("current_diet", sa.Text()),
]


def upgrade() -> None:
    for name, type_ in _COLUMNS:
        op.add_column("user_profiles", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    for name, _ in reversed(_COLUMNS):
        op.drop_column("user_profiles", name)
