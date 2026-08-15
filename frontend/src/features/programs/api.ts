import { http, MODEL_TIMEOUT_MS } from '../../services/httpClient'
import type {
  FatigueAnswers,
  FatigueAssessment,
  Profile,
  Program,
  ProgramAdjustment,
  ProgramReview,
  ProgramSummary,
} from '../../types/api'

export const programsApi = {
  list: () => http.get<ProgramSummary[]>('/programs'),
  get: (id: string) => http.get<Program>(`/programs/${id}`),
  /** The continuation verdict. Decided by the backend's plateau engine, never here. */
  review: (id: string) => http.get<ProgramReview>(`/programs/${id}/review`),
  /** Refused by the backend while something is stalling, and past the week cap. */
  extend: (id: string) => http.post<Program>(`/programs/${id}/extend`),
  archive: (id: string) => http.post<ProgramSummary>(`/programs/${id}/archive`),
  /** Applying a verdict. Each of these rewrites every week of the program, because the
   *  training rotation is served from the first week - see services/program_adjust.py. */
  swapExercise: (id: string, payload: { exercise_name: string; replacement_name: string }) =>
    http.post<ProgramAdjustment>(`/programs/${id}/exercises/swap`, payload),
  intensifyExercise: (id: string, exerciseName: string) =>
    http.post<ProgramAdjustment>(`/programs/${id}/exercises/intensify`, { exercise_name: exerciseName }),
  adjustMuscle: (id: string, muscleGroup: string) =>
    http.post<ProgramAdjustment>(`/programs/${id}/muscles/adjust`, { muscle_group: muscleGroup }),
  /** Designing a whole program takes the model 20-40 seconds; the default timeout would
   *  cut it off mid-answer and leave the user with nothing. */
  generate: (totalWeeks = 8) =>
    http.post<Program>('/programs/generate', { total_weeks: totalWeeks }, {
      timeoutMs: MODEL_TIMEOUT_MS,
    }),
  recalculate: () => http.post<Profile>('/profile/recalculate'),
  /** The deload decision is made by the backend from these answers, never here. */
  submitFatigue: (programId: string, payload: { week_number: number; answers: FatigueAnswers }) =>
    http.post<FatigueAssessment>(`/programs/${programId}/fatigue`, payload),
}
