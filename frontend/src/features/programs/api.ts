import { http } from '../../services/httpClient'
import type { FatigueAnswers, FatigueAssessment, Profile, Program } from '../../types/api'

export const programsApi = {
  generate: (totalWeeks = 8) =>
    http.post<Program>('/programs/generate', { total_weeks: totalWeeks }),
  recalculate: () => http.post<Profile>('/profile/recalculate'),
  /** The deload decision is made by the backend from these answers, never here. */
  submitFatigue: (programId: string, payload: { week_number: number; answers: FatigueAnswers }) =>
    http.post<FatigueAssessment>(`/programs/${programId}/fatigue`, payload),
}
