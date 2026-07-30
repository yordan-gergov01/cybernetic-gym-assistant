import { http } from '../../services/httpClient'
import type { WeightCoaching, WeightTrend } from '../../types/api'

export const progressApi = {
  trend: () => http.get<WeightTrend>('/weight/trend'),
  coaching: () => http.get<WeightCoaching>('/weight/coaching'),
  logWeight: (date: string, weightKg: number) => http.post('/weight', { date, weight_kg: weightKg }),
}
