import { http } from '../../services/httpClient'
import type { Program, WorkoutSetInput } from '../../types/api'

export type LogWorkoutPayload = {
  program_id: string
  day_id: string
  date: string
  sets: WorkoutSetInput[]
}

export const workoutsApi = {
  listPrograms: () => http.get<Program[]>('/programs'),
  getProgram: (id: string) => http.get<Program>(`/programs/${id}`),
  logWorkout: (payload: LogWorkoutPayload) => http.post('/workouts', payload),
  weekSummary: () => http.get<{ workouts_done: number; total_sets: number }>('/workouts/week/summary'),
}
