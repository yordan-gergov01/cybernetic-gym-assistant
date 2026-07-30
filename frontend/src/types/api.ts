// Mirrors backend/app/schemas.py. Kept hand-written and small: only the fields the
// UI actually reads, so a backend field rename shows up as a type error here.

export type AuthResponse = { access_token: string; user_id: string; name: string }

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

export type NutritionTargets = { calories: number; protein_g: number; fat_g: number; carbs_g: number }

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

export type Program = {
  id: string
  name: string
  description?: string | null
  total_weeks: number
  status: string
  goal?: string | null
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
