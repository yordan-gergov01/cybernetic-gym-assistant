import { http } from '../../services/httpClient'
import type { ExerciseStrength, WeightCoaching, WeightTrend } from '../../types/api'

export const progressApi = {
  /** `days` of 0 asks for the whole history; the window is applied before the trend is
   *  computed, so the chart and the rate always describe the same period. */
  trend: (days = 0) => http.get<WeightTrend>(`/weight/trend?days=${days}`),
  strength: (weeks = 4) => http.get<ExerciseStrength[]>(`/workouts/strength?weeks=${weeks}`),
  coaching: () => http.get<WeightCoaching>('/weight/coaching'),
  logWeight: (date: string, weightKg: number) => http.post('/weight', { date, weight_kg: weightKg }),
}
