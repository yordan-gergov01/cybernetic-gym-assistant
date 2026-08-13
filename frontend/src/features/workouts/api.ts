import { http } from '../../services/httpClient'
import type { TodayView, WorkoutLogSummary, WorkoutSetInput } from '../../types/api'

export type LogWorkoutPayload = {
  program_id: string
  day_id: string
  date: string
  sets: WorkoutSetInput[]
}

export const workoutsApi = {
  /** Everything the Today screen shows. The client renders it, it decides nothing. */
  today: () => http.get<TodayView>('/workouts/today'),
  /** Logged sessions, newest first. The program screen reads only `day_id` off them,
   *  to mark which days of the plan were actually trained. */
  list: (limit: number) => http.get<WorkoutLogSummary[]>(`/workouts?limit=${limit}`),
  logWorkout: (payload: LogWorkoutPayload) => http.post('/workouts', payload),
  weekSummary: () => http.get<{ workouts_done: number; total_sets: number }>('/workouts/week/summary'),
}
