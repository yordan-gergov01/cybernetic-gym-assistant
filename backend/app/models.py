import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

_TS = DateTime(timezone=True)


def new_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(_TS, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False)
    programs: Mapped[list["Program"]] = relationship(back_populates="user")
    weight_logs: Mapped[list["WeightLog"]] = relationship(back_populates="user")
    workout_logs: Mapped[list["WorkoutLog"]] = relationship(back_populates="user")
    food_logs: Mapped[list["FoodLog"]] = relationship(back_populates="user")
    chat_messages: Mapped[list["ChatMessage"]] = relationship(back_populates="user")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")
    photos: Mapped[list["UserPhoto"]] = relationship(back_populates="user")


class PasswordResetToken(Base):
    """A one-time key to an account, sent by email.

    Only a hash of the token is stored, for the same reason passwords are: whoever reads
    this table must not be able to walk into the accounts it belongs to. The row is kept
    after use so a link cannot be replayed.
    """

    __tablename__ = "password_reset_tokens"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(_TS)
    created_at: Mapped[datetime] = mapped_column(_TS, default=datetime.utcnow)

    user: Mapped["User"] = relationship()


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), unique=True)
    age: Mapped[int | None] = mapped_column(Integer)
    sex: Mapped[str | None] = mapped_column(String(10))
    height_cm: Mapped[float | None] = mapped_column(Float)
    bodyweight_kg: Mapped[float | None] = mapped_column(Float)
    body_fat_pct: Mapped[float | None] = mapped_column(Float)
    bf_assessment_method: Mapped[str | None] = mapped_column(String(50))
    goal: Mapped[str | None] = mapped_column(String(30))
    goal_validated: Mapped[str | None] = mapped_column(String(30))
    goal_details: Mapped[str | None] = mapped_column(Text)
    activity_level: Mapped[str | None] = mapped_column(String(20))
    activity_details: Mapped[str | None] = mapped_column(Text)
    training_status: Mapped[int | None] = mapped_column(Integer)
    training_years: Mapped[float | None] = mapped_column(Float)
    training_days_per_week: Mapped[int | None] = mapped_column(Integer)
    available_equipment: Mapped[str | None] = mapped_column(String(30))
    session_duration_min: Mapped[int | None] = mapped_column(Integer)
    lifts: Mapped[dict | None] = mapped_column(JSONB)
    priority_muscles: Mapped[list | None] = mapped_column(JSONB)
    injuries: Mapped[str | None] = mapped_column(Text)
    exercise_preferences: Mapped[str | None] = mapped_column(Text)
    dietary_restrictions: Mapped[str | None] = mapped_column(Text)

    # --- Henselmans coaching intake form ---------------------------------------
    # Fields below mirror the official PT client intake form. They are not cosmetic:
    # each one changes a coaching decision, so they are collected during onboarding.

    # Smallest load jump actually available in the user's gym. The progression engine
    # assumes 2.5 kg / 1.25 kg steps; if the lightest plates only allow 5 kg jumps,
    # prescribing +2.5 kg is impossible to follow.
    min_barbell_increment_kg: Mapped[float | None] = mapped_column(Float)
    min_dumbbell_increment_kg: Mapped[float | None] = mapped_column(Float)

    # Recovery capacity inputs — they cap how much volume can be tolerated and feed
    # the deload decision alongside the weekly check-in.
    stress_level: Mapped[str | None] = mapped_column(String(20))       # stress_free|mild|average|high
    sleep_quality: Mapped[str | None] = mapped_column(String(10))      # poor|fair|good
    sleep_hours: Mapped[float | None] = mapped_column(Float)

    # A/B/C in the intake form: how aggressively to push rate of progress.
    dedication_level: Mapped[str | None] = mapped_column(String(20))   # sustainable|balanced|maximal

    # "If you don't answer this accurately, you may get a program you can't follow."
    unavailable_times: Mapped[str | None] = mapped_column(Text)

    # Detailed equipment availability (rack, leg curl type, cable tower, bands, ...).
    equipment_details: Mapped[dict | None] = mapped_column(JSONB)

    # Inverse of priority_muscles — groups the user does NOT want to grow.
    avoid_growth_muscles: Mapped[list | None] = mapped_column(JSONB)

    # Sport/activity outside lifting: interference effect and recovery budget.
    other_activities: Mapped[str | None] = mapped_column(Text)

    # Occupation characterises circadian rhythm, stress and non-training activity.
    occupation: Mapped[str | None] = mapped_column(String(120))
    caffeine_mg_per_day: Mapped[int | None] = mapped_column(Integer)

    # Where the user is coming from, so the first program is a transition not a shock.
    current_program: Mapped[str | None] = mapped_column(Text)
    current_diet: Mapped[str | None] = mapped_column(Text)

    calculator_results: Mapped[dict | None] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(_TS, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="profile")


class Program(Base):
    __tablename__ = "programs"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(10), nullable=False)
    template_type: Mapped[str | None] = mapped_column(String(20))
    total_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active")
    goal: Mapped[str | None] = mapped_column(String(30))
    training_status: Mapped[int | None] = mapped_column(Integer)
    ai_context: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(_TS, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(_TS, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="programs")
    weeks: Mapped[list["ProgramWeek"]] = relationship(back_populates="program", cascade="all, delete-orphan")


class ProgramWeek(Base):
    __tablename__ = "program_weeks"
    __table_args__ = (UniqueConstraint("program_id", "week_number"),)
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    program_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("programs.id"))
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    week_type: Mapped[str] = mapped_column(String(20), default="loading")
    notes: Mapped[str | None] = mapped_column(Text)

    program: Mapped["Program"] = relationship(back_populates="weeks")
    days: Mapped[list["ProgramDay"]] = relationship(
        back_populates="week",
        cascade="all, delete-orphan",
        order_by="ProgramDay.day_number",
    )


class ProgramDay(Base):
    __tablename__ = "program_days"
    __table_args__ = (UniqueConstraint("week_id", "day_number"),)
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    week_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("program_weeks.id"))
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    day_name: Mapped[str | None] = mapped_column(String(50))
    is_rest_day: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)

    week: Mapped["ProgramWeek"] = relationship(back_populates="days")
    # Ordered by the relationship itself: a day is a sequence of exercises, and without
    # this the API returns whatever order the rows happen to come back in - which changes
    # the moment one of them is updated.
    exercises: Mapped[list["ProgramExercise"]] = relationship(
        back_populates="day",
        cascade="all, delete-orphan",
        order_by="ProgramExercise.order_index",
    )


class ProgramExercise(Base):
    __tablename__ = "program_exercises"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    day_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("program_days.id"))
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    exercise_name: Mapped[str] = mapped_column(String(200), nullable=False)
    muscle_group: Mapped[str | None] = mapped_column(String(50))
    equipment: Mapped[str | None] = mapped_column(String(50))
    sets_prescribed: Mapped[int | None] = mapped_column(Integer)
    reps_min: Mapped[int | None] = mapped_column(Integer)
    reps_max: Mapped[int | None] = mapped_column(Integer)
    rir_target: Mapped[int | None] = mapped_column(Integer)
    rest_seconds: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    target_weight_kg: Mapped[float | None] = mapped_column(Float)
    target_reps: Mapped[int | None] = mapped_column(Integer)
    target_note: Mapped[str | None] = mapped_column(Text)

    day: Mapped["ProgramDay"] = relationship(back_populates="exercises")


class FatigueAssessment(Base):
    __tablename__ = "fatigue_assessments"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    program_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("programs.id"))
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    answers: Mapped[dict] = mapped_column(JSONB, nullable=False)
    agent_decision: Mapped[str | None] = mapped_column(String(20))
    agent_reasoning: Mapped[str | None] = mapped_column(Text)
    assessed_at: Mapped[datetime] = mapped_column(_TS, default=datetime.utcnow)


class WorkoutLog(Base):
    __tablename__ = "workout_logs"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    program_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("programs.id"))
    day_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("program_days.id"))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(_TS)
    finished_at: Mapped[datetime | None] = mapped_column(_TS)
    duration_min: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="completed")

    user: Mapped["User"] = relationship(back_populates="workout_logs")
    sets: Mapped[list["WorkoutSet"]] = relationship(back_populates="workout_log", cascade="all, delete-orphan")


class WorkoutSet(Base):
    __tablename__ = "workout_sets"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    workout_log_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("workout_logs.id"))
    program_exercise_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("program_exercises.id"))
    exercise_name: Mapped[str] = mapped_column(String(200), nullable=False)
    set_number: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    reps: Mapped[int | None] = mapped_column(Integer)
    rir_actual: Mapped[int | None] = mapped_column(Integer)
    is_warmup: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)

    workout_log: Mapped["WorkoutLog"] = relationship(back_populates="sets")


class WeightLog(Base):
    __tablename__ = "weight_logs"
    __table_args__ = (UniqueConstraint("user_id", "date"),)
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    logged_at: Mapped[datetime] = mapped_column(_TS, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="weight_logs")


class FoodLog(Base):
    __tablename__ = "food_logs"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    meal_type: Mapped[str | None] = mapped_column(String(20))
    food_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity_g: Mapped[float | None] = mapped_column(Float)
    calories: Mapped[float | None] = mapped_column(Float)
    protein_g: Mapped[float | None] = mapped_column(Float)
    fat_g: Mapped[float | None] = mapped_column(Float)
    carbs_g: Mapped[float | None] = mapped_column(Float)
    sugar_g: Mapped[float | None] = mapped_column(Float)
    fiber_g: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(50))
    confidence: Mapped[str | None] = mapped_column(String(10))
    logged_at: Mapped[datetime] = mapped_column(_TS, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="food_logs")


class NutritionTarget(Base):
    __tablename__ = "nutrition_targets"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), unique=True)
    calories: Mapped[int | None] = mapped_column(Integer)
    protein_g: Mapped[int | None] = mapped_column(Integer)
    fat_g: Mapped[int | None] = mapped_column(Integer)
    carbs_g: Mapped[int | None] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(_TS, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(_TS, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="chat_messages")


class AiInteraction(Base):
    """One row per call to a model: what was asked, what was retrieved, what it cost.

    Without it the only record of a coaching answer is the answer itself, which cannot
    say which course passages produced it, which prompt version was live, or whether the
    user waited two seconds or twenty. Retrieved passages are stored as chunk ids and
    scores rather than as text: the ids reconstruct the exact context from the index, and
    the course material stays out of the application database.

    A failed call is recorded too - a trace that only covers successes hides precisely
    the requests worth investigating.
    """

    __tablename__ = "ai_interactions"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), index=True)
    # Which flow asked: chat | program | fatigue. Metrics are only useful broken down by it.
    surface: Mapped[str] = mapped_column(String(30), nullable=False)
    # The answer this trace explains, when the flow stores one.
    message_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("chat_messages.id"))

    query: Mapped[str] = mapped_column(Text, nullable=False)
    # What retrieval actually searched on after the follow-up was resolved.
    resolved_query: Mapped[str | None] = mapped_column(Text)
    retrieved: Mapped[list | None] = mapped_column(JSONB)

    prompt_name: Mapped[str | None] = mapped_column(String(50))
    prompt_version: Mapped[str | None] = mapped_column(String(10))
    model: Mapped[str | None] = mapped_column(String(60))
    temperature: Mapped[float | None] = mapped_column(Float)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)

    retrieval_ms: Mapped[int | None] = mapped_column(Integer)
    generation_ms: Mapped[int | None] = mapped_column(Integer)
    total_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(_TS, default=datetime.utcnow, index=True)

    user: Mapped["User"] = relationship()


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    body: Mapped[str | None] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    scheduled_for: Mapped[datetime | None] = mapped_column(_TS)
    created_at: Mapped[datetime] = mapped_column(_TS, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="notifications")


class UserPhoto(Base):
    __tablename__ = "user_photos"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    photo_type: Mapped[str | None] = mapped_column(String(20))   # e.g. progress | bf_assessment
    angle: Mapped[str | None] = mapped_column(String(10))        # front | back | side
    file_path: Mapped[str | None] = mapped_column(String(500))   # R2 object key (NOT the binary)
    bf_pct_assessed: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    taken_at: Mapped[date] = mapped_column(Date, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="photos")
