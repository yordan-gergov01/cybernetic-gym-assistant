// Mirrors backend/app/schemas.py. Kept hand-written and small: only the fields the
// UI actually reads, so a backend field rename shows up as a type error here.

export type AuthResponse = { access_token: string; user_id: string; name: string }

/** Mirrors backend ProfileCreate, including the Henselmans intake fields. */
export type ProfileCreate = {
  age: number
  sex: 'male' | 'female'
  height_cm: number
  bodyweight_kg: number
  body_fat_pct?: number | null
  goal: 'bulk' | 'cut' | 'maintain' | 'aggressive_cut'
  goal_details?: string | null
  activity_level: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active'
  activity_details?: string | null
  training_status: 1 | 2 | 3
  training_years: number
  training_days_per_week: number
  available_equipment: 'full_gym' | 'home_gym' | 'dumbbells_only' | 'bodyweight'
  session_duration_min: number
  lifts?: Record<string, { weight: number; reps: number }> | null
  priority_muscles?: string[] | null
  injuries?: string | null
  exercise_preferences?: string | null
  dietary_restrictions?: string | null
  // intake form additions
  min_barbell_increment_kg?: number | null
  min_dumbbell_increment_kg?: number | null
  stress_level?: 'stress_free' | 'mild' | 'average' | 'high' | null
  sleep_quality?: 'poor' | 'fair' | 'good' | null
  sleep_hours?: number | null
  dedication_level?: 'sustainable' | 'balanced' | 'maximal' | null
  unavailable_times?: string | null
  equipment_details?: Record<string, boolean | string> | null
  avoid_growth_muscles?: string[] | null
  other_activities?: string | null
  occupation?: string | null
  caffeine_mg_per_day?: number | null
  current_program?: string | null
  current_diet?: string | null
}

export type Profile = {
  id: string
  age: number
  sex: string
  height_cm: number
  bodyweight_kg: number
  body_fat_pct?: number | null
  goal: string
  goal_validated?: string | null
  bf_assessment_method?: string | null
  training_status: number
  training_days_per_week: number
  priority_muscles?: string[] | null
  calculator_results?: {
    energy?: { target_kcal?: number; protein_g?: number; fat_g?: number; carbs_g?: number; tdee_kcal?: number }
    volume?: Record<string, number>
  } | null
}

export type PhotoAngle = 'front' | 'side' | 'back'

export type UserPhoto = {
  id: string
  photo_type?: string | null
  angle?: PhotoAngle | null
  bf_pct_assessed?: number | null
  taken_at: string
  /** Time-limited presigned URL; absent when storage could not sign it. */
  url?: string | null
}

/** POST /photos/assess-bf. The range and confidence are part of the answer, not
 *  decoration - a low-confidence read must stay visible to the user. */
export type BFAssessment = {
  bf_pct: number
  range_low: number
  range_high: number
  confidence: 'high' | 'medium' | 'low'
  observed_markers: string[]
  closest_reference: string
  limitations: string
  reasoning_bg: string
  model: string
  photo_count: number
  applied_to_profile: boolean
}

export type NutritionTargets ={ calories: number; protein_g: number; fat_g: number; carbs_g: number }

export type FoodEntry = {
  id: string
  meal_type?: string | null
  food_name: string
  quantity_g?: number | null
  calories?: number | null
  protein_g?: number | null
  fat_g?: number | null
  carbs_g?: number | null
  /** "USDA" when the numbers came from the food database, "LLM estimate" when they
   *  were estimated - the UI says so rather than presenting a guess as a fact. */
  source?: string | null
  confidence?: string | null
}

export type DailyNutrition = {
  date: string
  entries: FoodEntry[]
  totals: Record<string, number>
  targets: Record<string, number>
  remaining: Record<string, number>
  pct_complete: Record<string, number>
}

export type WeightTrend = {
  status: 'ok' | 'insufficient_data'
  current_weight?: number
  weekly_rate_kg?: number
  direction?: 'up' | 'down' | 'stable'
  trend_points?: { date: string; ewma: number; raw: number }[]
  total_entries?: number
}

export type WeightCoaching = {
  status: 'ok' | 'insufficient_data'
  message?: string
  current_weight?: number
  weekly_rate_kg?: number
  direction?: string
  goal?: string
  target_weekly_rate_kg?: number
  on_track?: boolean
  calorie_delta?: number
  new_calorie_target?: number | null
  recommendation?: string
}

export type ProgramExercise = {
  id: string
  order_index: number
  exercise_name: string
  muscle_group?: string | null
  sets_prescribed?: number | null
  reps_min?: number | null
  reps_max?: number | null
  rir_target?: number | null
  rest_seconds?: number | null
  target_weight_kg?: number | null
  target_reps?: number | null
  target_note?: string | null
}

export type ProgramDay = {
  id: string
  day_number: number
  day_name?: string | null
  is_rest_day: boolean
  exercises: ProgramExercise[]
}

export type ProgramWeek = { id: string; week_number: number; week_type: string; days: ProgramDay[] }

/** GET /programs — list view, no nested weeks (see backend ProgramSummary). */
export type ProgramSummary = {
  id: string
  name: string
  description?: string | null
  template_type?: string | null
  total_weeks: number
  status: string
  goal?: string | null
  start_date?: string | null
  end_date?: string | null
  created_at: string
}

/** GET /programs/{id} — the full tree. */
export type Program = ProgramSummary & {
  weeks: ProgramWeek[]
}

/** GET /programs/{id}/review — the plateau engine's verdict on the program.
 *  Every field here is decided deterministically by the backend (domain/plateau.py). */
export type ProgramAction =
  | 'extend'
  | 'adjust_exercise'
  | 'adjust_muscle'
  | 'check_recovery'
  | 'complete'

export type ExerciseProgress = {
  exercise_name: string
  muscle_group?: string | null
  status: 'progressing' | 'holding' | 'stalled' | 'insufficient_data'
  sessions_since_best: number
  best_e1rm?: number | null
  latest_e1rm?: number | null
  change_pct?: number | null
}

/** The heavier session prescribed to break a single missed progression. */
export type PlateauBreaker = { exercise_name: string; weight_kg: number; reps: number }

export type ProgramReview = {
  action: ProgramAction
  scope?: 'systemic' | 'local_muscle' | 'local_exercise' | null
  reason_bg: string
  muscle_group?: string | null
  exercise_name?: string | null
  new_rep_target?: number | null
  total_weeks: number
  max_weeks: number
  exercises: ExerciseProgress[]
  breakers: PlateauBreaker[]
  sessions_analysed: number
  /** Prescribed exercises with no usable work sets — shown, never silently dropped. */
  skipped_exercises: string[]
}

/** GET /exercises — one entry of the course exercise library. */
export type Exercise = {
  name: string
  category: string
  region: string
  muscle_group?: string | null
  cues: string[]
}

/** GET /workouts/today — the whole Today screen, decided by the backend. */
export type CalendarDay = { date: string; trained: boolean; is_today: boolean }

export type SessionEstimate = { exercise_count: number; total_sets: number; minutes: number }

export type MuscleVolume = { muscle_group: string; sets_done: number; sets_target: number | null }

export type LastSession = { date: string; tonnage_kg: number; working_sets: number }

export type TodayView = {
  program_id: string
  program_name: string
  template_type?: string | null
  goal?: string | null
  week_number: number
  total_weeks: number
  is_rest_day: boolean
  trained_today: boolean
  weighed_in_today: boolean
  sessions_this_week: number
  sessions_planned: number
  calendar: CalendarDay[]
  day_id?: string | null
  day_name?: string | null
  exercises: ProgramExercise[]
  estimate?: SessionEstimate | null
  last_session?: LastSession | null
  weekly_volume: MuscleVolume[]
}

/** GET /workouts/strength — estimated max per exercise over a window. */
export type ExerciseStrength = {
  exercise_name: string
  muscle_group?: string | null
  best_e1rm: number
  change_kg: number
  sessions: number
  points: number[]
}

/** GET /workouts — only the fields the program screen reads off a logged session.
 *  `day_id` is what marks a program day as trained; the sets themselves are not used. */
export type WorkoutLogSummary = {
  id: string
  program_id?: string | null
  day_id?: string | null
  date: string
  status: string
}

export type WorkoutSetInput = {
  program_exercise_id?: string | null
  exercise_name: string
  set_number: number
  weight_kg?: number | null
  reps?: number | null
  rir_actual?: number | null
  is_warmup?: boolean
}

export type Notification = {
  id: string
  type: string
  title?: string | null
  body?: string | null
  is_read: boolean
  created_at: string
}

/** POST /programs/{id}/fatigue — the weekly recovery check-in. */
export type FatigueAnswers = {
  recovery_quality: 'poor' | 'fair' | 'good'
  performance_trend: 'declining' | 'stable' | 'improving'
  joint_pain: boolean
  sleep_quality: 'poor' | 'fair' | 'good'
  motivation: 'low' | 'moderate' | 'high'
  appetite: 'decreased' | 'normal' | 'increased'
}

export type FatigueAssessment = {
  id: string
  week_number: number
  agent_decision: 'continue' | 'caution' | 'deload'
  agent_reasoning?: string | null
  assessed_at: string
}

export type ChatMessage = { id: string; role: 'user' | 'assistant'; content: string; created_at: string }
