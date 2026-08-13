import { http } from '../../services/httpClient'
import type {
  FatigueAnswers,
  FatigueAssessment,
  Profile,
  Program,
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
  generate: (totalWeeks = 8) =>
    http.post<Program>('/programs/generate', { total_weeks: totalWeeks }),
  recalculate: () => http.post<Profile>('/profile/recalculate'),
  /** The deload decision is made by the backend from these answers, never here. */
  submitFatigue: (programId: string, payload: { week_number: number; answers: FatigueAnswers }) =>
    http.post<FatigueAssessment>(`/programs/${programId}/fatigue`, payload),
}
