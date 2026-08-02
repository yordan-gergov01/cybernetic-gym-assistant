import { http } from '../../services/httpClient'
import { todayIso } from '../../utils/date'
import type { BFAssessment, PhotoAngle, UserPhoto } from '../../types/api'

export const photosApi = {
  upload: (file: File, angle: PhotoAngle, photoType = 'bf_assessment') => {
    const form = new FormData()
    form.append('file', file)
    form.append('taken_at', todayIso())
    form.append('photo_type', photoType)
    form.append('angle', angle)
    return http.post<UserPhoto>('/photos', form)
  },

  /** `sex` is only read by the backend while no profile exists yet (onboarding); it
   *  anchors the visual rubric to the right reference set. */
  assessBf: (payload: { photo_ids: string[]; apply_to_profile: boolean; sex?: 'male' | 'female' }) =>
    http.post<BFAssessment>('/photos/assess-bf', payload),

  remove: (id: string) => http.delete<void>(`/photos/${id}`),
}
