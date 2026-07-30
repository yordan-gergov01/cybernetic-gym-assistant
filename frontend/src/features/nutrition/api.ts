import { http } from '../../services/httpClient'
import type { DailyNutrition } from '../../types/api'

export const nutritionApi = {
  daily: (date: string) => http.get<DailyNutrition>(`/food/daily/${date}`),
  logFood: (date: string, description: string) =>
    http.post('/food', { date, food_description: description }),
  deleteEntry: (id: string) => http.delete(`/food/${id}`),
}
