import { http, MODEL_TIMEOUT_MS } from '../../services/httpClient'
import { todayIso } from '../../utils/date'
import type { BFAssessment, PhotoAngle, UserPhoto } from '../../types/api'

export const photosApi = {
  list: () => http.get<UserPhoto[]>('/photos'),
  upload: (file: File, angle: PhotoAngle, photoType = 'bf_assessment') => {
    const form = new FormData()
    form.append('file', file)
    form.append('taken_at', todayIso())
    form.append('photo_type', photoType)
    form.append('angle', angle)
    // Photos are megabytes over a gym connection; the upload gets the long timeout for
    // the transfer itself, not because anything is thinking about it.
    return http.post<UserPhoto>('/photos', form, { timeoutMs: MODEL_TIMEOUT_MS })
  },

  /** `sex` is only read by the backend while no profile exists yet (onboarding); it
   *  anchors the visual rubric to the right reference set. */
  assessBf: (payload: { photo_ids: string[]; apply_to_profile: boolean; sex?: 'male' | 'female' }) =>
    http.post<BFAssessment>('/photos/assess-bf', payload, { timeoutMs: MODEL_TIMEOUT_MS }),

  remove: (id: string) => http.delete<void>(`/photos/${id}`),
}
