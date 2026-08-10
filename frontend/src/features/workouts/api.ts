import { http } from '../../services/httpClient'
import type { Program, ProgramSummary, TodayView, WorkoutSetInput } from '../../types/api'

export type LogWorkoutPayload = {
  program_id: string
  day_id: string
  date: string
  sets: WorkoutSetInput[]
}

export const workoutsApi = {
  /** Everything the Today screen shows. The client renders it, it decides nothing. */
  today: () => http.get<TodayView>('/workouts/today'),
  listPrograms: () => http.get<ProgramSummary[]>('/programs'),
  getProgram: (id: string) => http.get<Program>(`/programs/${id}`),
  logWorkout: (payload: LogWorkoutPayload) => http.post('/workouts', payload),
  weekSummary: () => http.get<{ workouts_done: number; total_sets: number }>('/workouts/week/summary'),
}
