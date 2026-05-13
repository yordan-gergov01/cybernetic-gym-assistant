from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import Optional

# AUTH
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str

class UserOut(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime
    class Config: from_attributes = True

# PROFILE
class LiftEntry(BaseModel):
    weight: float
    reps: int

class ProfileCreate(BaseModel):
    age: int
    sex: str
    height_cm: float
    bodyweight_kg: float
    body_fat_pct: Optional[float] = None
    goal: str
    goal_details: Optional[str] = None
    activity_level: str
    activity_details: Optional[str] = None
    training_status: int = Field(ge=1, le=3)
    training_years: float
    training_days_per_week: int = Field(ge=1, le=7)
    available_equipment: str
    session_duration_min: int
    lifts: Optional[dict[str, LiftEntry]] = None
    priority_muscles: Optional[list[str]] = None
    injuries: Optional[str] = None
    exercise_preferences: Optional[str] = None
    dietary_restrictions: Optional[str] = None

class ProfileOut(ProfileCreate):
    id: str
    user_id: str
    goal_validated: Optional[str] = None
    bf_assessment_method: Optional[str] = None
    calculator_results: Optional[dict] = None
    updated_at: datetime
    class Config: from_attributes = True

# WEIGHT
class WeightLogCreate(BaseModel):
    date: date
    weight_kg: float = Field(gt=0, lt=500)
    notes: Optional[str] = None

class WeightLogOut(WeightLogCreate):
    id: str
    user_id: str
    logged_at: datetime
    class Config: from_attributes = True

class WeightTrend(BaseModel):
    entries: list[WeightLogOut]
    weekly_averages: list[dict]
    trend: dict

# FOOD
class FoodLogCreate(BaseModel):
    date: date
    meal_type: Optional[str] = None
    food_description: str   # raw text - parsed by LLM+USDA

class FoodEntryOut(BaseModel):
    id: str
    food_name: str
    quantity_g: Optional[float]
    calories: Optional[float]
    protein_g: Optional[float]
    fat_g: Optional[float]
    carbs_g: Optional[float]
    source: Optional[str]
    confidence: Optional[str]
    logged_at: datetime
    class Config: from_attributes = True

class DailyNutritionSummary(BaseModel):
    date: date
    entries: list[FoodEntryOut]
    totals: dict
    targets: dict
    remaining: dict
    pct_complete: dict

# NUTRITION TARGETS
class NutritionTargetCreate(BaseModel):
    calories: int
    protein_g: int
    fat_g: int
    carbs_g: int

class NutritionTargetOut(NutritionTargetCreate):
    id: str
    user_id: str
    updated_at: datetime
    class Config: from_attributes = True

# PROGRAM
class ProgramExerciseCreate(BaseModel):
    order_index: int
    exercise_name: str
    muscle_group: Optional[str] = None
    equipment: Optional[str] = None
    sets_prescribed: Optional[int] = None
    reps_min: Optional[int] = None
    reps_max: Optional[int] = None
    rir_target: Optional[int] = None
    rest_seconds: Optional[int] = None
    notes: Optional[str] = None

class ProgramExerciseOut(ProgramExerciseCreate):
    id: str
    day_id: str
    target_weight_kg: Optional[float] = None
    target_reps: Optional[int] = None
    target_note: Optional[str] = None
    class Config: from_attributes = True

class ProgramDayCreate(BaseModel):
    day_number: int
    day_name: Optional[str] = None
    is_rest_day: bool = False
    notes: Optional[str] = None
    exercises: list[ProgramExerciseCreate] = []

class ProgramDayOut(ProgramDayCreate):
    id: str
    week_id: str
    exercises: list[ProgramExerciseOut] = []
    class Config: from_attributes = True

class ProgramWeekCreate(BaseModel):
    week_number: int
    week_type: str = "loading"
    notes: Optional[str] = None
    days: list[ProgramDayCreate] = []

class ProgramWeekOut(ProgramWeekCreate):
    id: str
    program_id: str
    days: list[ProgramDayOut] = []
    class Config: from_attributes = True

class ProgramCreate(BaseModel):
    name: str
    description: Optional[str] = None
    created_by: str = "manual"
    template_type: Optional[str] = None
    total_weeks: int = Field(ge=1, le=52)
    start_date: Optional[date] = None
    weeks: list[ProgramWeekCreate] = []

class ProgramOut(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    created_by: str
    template_type: Optional[str]
    total_weeks: int
    start_date: Optional[date]
    end_date: Optional[date]
    status: str
    goal: Optional[str]
    created_at: datetime
    weeks: list[ProgramWeekOut] = []
    class Config: from_attributes = True

class ProgramGenerateRequest(BaseModel):
    total_weeks: int = 8
    start_date: Optional[date] = None
    additional_notes: Optional[str] = None

# WORKOUT
class WorkoutSetCreate(BaseModel):
    program_exercise_id: Optional[str] = None
    exercise_name: str
    set_number: int
    weight_kg: Optional[float] = None
    reps: Optional[int] = None
    rir_actual: Optional[int] = None
    is_warmup: bool = False
    notes: Optional[str] = None

class WorkoutSetOut(WorkoutSetCreate):
    id: str
    workout_log_id: str
    class Config: from_attributes = True

class WorkoutLogCreate(BaseModel):
    program_id: Optional[str] = None
    day_id: Optional[str] = None
    date: date
    notes: Optional[str] = None
    sets: list[WorkoutSetCreate] = []

class WorkoutLogOut(BaseModel):
    id: str
    user_id: str
    program_id: Optional[str]
    day_id: Optional[str]
    date: date
    duration_min: Optional[int]
    notes: Optional[str]
    status: str
    sets: list[WorkoutSetOut] = []
    class Config: from_attributes = True

# CHAT
class ChatMessageCreate(BaseModel):
    content: str

class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    class Config: from_attributes = True

class ChatResponse(BaseModel):
    answer: str
    message_id: str

# NOTIFICATIONS
class NotificationOut(BaseModel):
    id: str
    type: str
    title: Optional[str]
    body: Optional[str]
    is_read: bool
    scheduled_for: Optional[datetime]
    created_at: datetime
    class Config: from_attributes = True

# FATIGUE ASSESSMENT
class FatigueAnswers(BaseModel):
    recovery_quality: str       # poor | fair | good
    performance_trend: str      # declining | stable | improving
    joint_pain: bool
    sleep_quality: str          # poor | fair | good
    motivation: str             # low | moderate | high
    appetite: str               # decreased | normal | increased

class FatigueAssessmentCreate(BaseModel):
    program_id: str
    week_number: int
    answers: FatigueAnswers

class FatigueAssessmentOut(BaseModel):
    id: str
    week_number: int
    answers: dict
    agent_decision: Optional[str]
    agent_reasoning: Optional[str]
    assessed_at: datetime
    class Config: from_attributes = True
