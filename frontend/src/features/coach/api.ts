import { http, MODEL_TIMEOUT_MS } from '../../services/httpClient'
import type { ChatMessage } from '../../types/api'

export const coachApi = {
  history: (limit = 50) => http.get<ChatMessage[]>(`/chat/history?limit=${limit}`),
  /** Retrieval plus the model: seconds, not milliseconds. */
  send: (content: string) =>
    http.post<{ answer: string; message_id: string }>('/chat', { content }, {
      timeoutMs: MODEL_TIMEOUT_MS,
    }),
  clear: () => http.delete('/chat/history'),
}
