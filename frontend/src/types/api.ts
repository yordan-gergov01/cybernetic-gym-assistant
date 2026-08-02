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
  training_status: number
  training_days_per_week: number
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

export type DailyNutrition = {
  date: string
  entries: { id: string; food_name: string; calories?: number; protein_g?: number; quantity_g?: number }[]
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
  total_weeks: number
  status: string
  goal?: string | null
  created_at: string
}

/** GET /programs/{id} — the full tree. */
export type Program = ProgramSummary & {
  weeks: ProgramWeek[]
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

export type ChatMessage = { id: string; role: 'user' | 'assistant'; content: string; created_at: string }
