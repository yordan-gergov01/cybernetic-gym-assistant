import { http } from '../../services/httpClient'
import type { ChatMessage } from '../../types/api'

export const coachApi = {
  history: (limit = 50) => http.get<ChatMessage[]>(`/chat/history?limit=${limit}`),
  send: (content: string) => http.post<{ answer: string; message_id: string }>('/chat', { content }),
  clear: () => http.delete('/chat/history'),
}
