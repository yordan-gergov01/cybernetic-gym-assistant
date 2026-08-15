import { http, MODEL_TIMEOUT_MS } from '../../services/httpClient'
import type { DailyNutrition } from '../../types/api'

export const nutritionApi = {
  daily: (date: string) => http.get<DailyNutrition>(`/food/daily/${date}`),
  /** Parsing free text into foods goes through the model and the food database, so it
   *  gets the long timeout - a slow answer here is normal, not a fault. */
  logFood: (date: string, description: string, mealType?: string) =>
    http.post('/food', { date, food_description: description, meal_type: mealType }, {
      timeoutMs: MODEL_TIMEOUT_MS,
    }),
  deleteEntry: (id: string) => http.delete(`/food/${id}`),
}
