import { http } from '../../services/httpClient'
import type { Profile, ProfileCreate } from '../../types/api'

export const profileApi = {
  get: () => http.get<Profile>('/profile'),
  update: (payload: ProfileCreate) => http.put<Profile>('/profile', payload),
  nutritionTargets: () => http.get<{ calories: number; protein_g: number }>('/profile/nutrition-targets'),
}
