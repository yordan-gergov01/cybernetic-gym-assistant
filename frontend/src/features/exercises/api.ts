import { http } from '../../services/httpClient'
import type { Exercise } from '../../types/api'

export const exercisesApi = {
  /** The backend also takes a `search` needle, but the screen filters by name in the
   *  client instead: the same substring rule over a list of 147 that is already loaded,
   *  without a request per keystroke. */
  list: (filters: { category?: string; muscle_group?: string } = {}) => {
    const params = new URLSearchParams()
    if (filters.category) params.set('category', filters.category)
    if (filters.muscle_group) params.set('muscle_group', filters.muscle_group)
    const query = params.toString()
    return http.get<Exercise[]>(`/exercises${query ? `?${query}` : ''}`)
  },
  categories: () => http.get<string[]>('/exercises/categories'),
  /** Swaps for one exercise: the guide's siblings under the same movement pattern.
   *  404 means the name is not in the course library at all - the caller has to say so
   *  rather than show an empty list, which would read as "there is no alternative". */
  alternatives: (name: string) =>
    http.get<Exercise[]>(`/exercises/alternatives?name=${encodeURIComponent(name)}`),
}
