import { http } from '../../services/httpClient'
import type { Profile, Program } from '../../types/api'

export const programsApi = {
  generate: (totalWeeks = 8) =>
    http.post<Program>('/programs/generate', { total_weeks: totalWeeks }),
  recalculate: () => http.post<Profile>('/profile/recalculate'),
}
