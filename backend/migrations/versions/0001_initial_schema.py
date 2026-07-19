"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-19

Creates the full baseline schema (14 tables) matching backend/src/models.py.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid():
    return postgresql.UUID(as_uuid=False)


def _ts():
    return sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", _ts(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "user_profiles",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("user_id", _uuid(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("sex", sa.String(10), nullable=True),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("bodyweight_kg", sa.Float(), nullable=True),
        sa.Column("body_fat_pct", sa.Float(), nullable=True),
        sa.Column("bf_assessment_method", sa.String(50), nullable=True),
        sa.Column("goal", sa.String(30), nullable=True),
        sa.Column("goal_validated", sa.String(30), nullable=True),
        sa.Column("goal_details", sa.Text(), nullable=True),
        sa.Column("activity_level", sa.String(20), nullable=True),
        sa.Column("activity_details", sa.Text(), nullable=True),
        sa.Column("training_status", sa.Integer(), nullable=True),
        sa.Column("training_years", sa.Float(), nullable=True),
        sa.Column("training_days_per_week", sa.Integer(), nullable=True),
        sa.Column("available_equipment", sa.String(30), nullable=True),
        sa.Column("session_duration_min", sa.Integer(), nullable=True),
        sa.Column("lifts", postgresql.JSONB(), nullable=True),
        sa.Column("priority_muscles", postgresql.JSONB(), nullable=True),
        sa.Column("injuries", sa.Text(), nullable=True),
        sa.Column("exercise_preferences", sa.Text(), nullable=True),
        sa.Column("dietary_restrictions", sa.Text(), nullable=True),
        sa.Column("calculator_results", postgresql.JSONB(), nullable=True),
        sa.Column("updated_at", _ts(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "programs",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("user_id", _uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(10), nullable=False),
        sa.Column("template_type", sa.String(20), nullable=True),
        sa.Column("total_weeks", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("goal", sa.String(30), nullable=True),
        sa.Column("training_status", sa.Integer(), nullable=True),
        sa.Column("ai_context", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
        sa.Column("updated_at", _ts(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "program_weeks",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("program_id", _uuid(), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("week_type", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("program_id", "week_number"),
    )

    op.create_table(
        "program_days",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("week_id", _uuid(), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("day_name", sa.String(50), nullable=True),
        sa.Column("is_rest_day", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["week_id"], ["program_weeks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("week_id", "day_number"),
    )

    op.create_table(
        "program_exercises",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("day_id", _uuid(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("exercise_name", sa.String(200), nullable=False),
        sa.Column("muscle_group", sa.String(50), nullable=True),
        sa.Column("equipment", sa.String(50), nullable=True),
        sa.Column("sets_prescribed", sa.Integer(), nullable=True),
        sa.Column("reps_min", sa.Integer(), nullable=True),
        sa.Column("reps_max", sa.Integer(), nullable=True),
        sa.Column("rir_target", sa.Integer(), nullable=True),
        sa.Column("rest_seconds", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("target_weight_kg", sa.Float(), nullable=True),
        sa.Column("target_reps", sa.Integer(), nullable=True),
        sa.Column("target_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["day_id"], ["program_days.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "fatigue_assessments",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("user_id", _uuid(), nullable=False),
        sa.Column("program_id", _uuid(), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("answers", postgresql.JSONB(), nullable=False),
        sa.Column("agent_decision", sa.String(20), nullable=True),
        sa.Column("agent_reasoning", sa.Text(), nullable=True),
        sa.Column("assessed_at", _ts(), nullable=False),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "workout_logs",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("user_id", _uuid(), nullable=False),
        sa.Column("program_id", _uuid(), nullable=True),
        sa.Column("day_id", _uuid(), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("started_at", _ts(), nullable=True),
        sa.Column("finished_at", _ts(), nullable=True),
        sa.Column("duration_min", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.ForeignKeyConstraint(["day_id"], ["program_days.id"]),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "workout_sets",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("workout_log_id", _uuid(), nullable=False),
        sa.Column("program_exercise_id", _uuid(), nullable=True),
        sa.Column("exercise_name", sa.String(200), nullable=False),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("reps", sa.Integer(), nullable=True),
        sa.Column("rir_actual", sa.Integer(), nullable=True),
        sa.Column("is_warmup", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["program_exercise_id"], ["program_exercises.id"]),
        sa.ForeignKeyConstraint(["workout_log_id"], ["workout_logs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "weight_logs",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("user_id", _uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("logged_at", _ts(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "date"),
    )

    op.create_table(
        "food_logs",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("user_id", _uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("meal_type", sa.String(20), nullable=True),
        sa.Column("food_name", sa.String(200), nullable=False),
        sa.Column("quantity_g", sa.Float(), nullable=True),
        sa.Column("calories", sa.Float(), nullable=True),
        sa.Column("protein_g", sa.Float(), nullable=True),
        sa.Column("fat_g", sa.Float(), nullable=True),
        sa.Column("carbs_g", sa.Float(), nullable=True),
        sa.Column("sugar_g", sa.Float(), nullable=True),
        sa.Column("fiber_g", sa.Float(), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("confidence", sa.String(10), nullable=True),
        sa.Column("logged_at", _ts(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "nutrition_targets",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("user_id", _uuid(), nullable=False),
        sa.Column("calories", sa.Integer(), nullable=True),
        sa.Column("protein_g", sa.Integer(), nullable=True),
        sa.Column("fat_g", sa.Integer(), nullable=True),
        sa.Column("carbs_g", sa.Integer(), nullable=True),
        sa.Column("updated_at", _ts(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("user_id", _uuid(), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", _ts(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("user_id", _uuid(), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("scheduled_for", _ts(), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("chat_messages")
    op.drop_table("nutrition_targets")
    op.drop_table("food_logs")
    op.drop_table("weight_logs")
    op.drop_table("workout_sets")
    op.drop_table("workout_logs")
    op.drop_table("fatigue_assessments")
    op.drop_table("program_exercises")
    op.drop_table("program_days")
    op.drop_table("program_weeks")
    op.drop_table("programs")
    op.drop_table("user_profiles")
    op.drop_table("users")
