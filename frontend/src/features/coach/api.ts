import { http, streamEvents } from '../../services/httpClient'
import type { ChatMessage } from '../../types/api'

/** What the coach sends back while it answers.
 *
 *  `done` means the turn is stored and the history now holds it; `error` means nothing
 *  was stored at all, so whatever arrived before it has to be thrown away. */
export type CoachEvent =
  | { type: 'delta'; text: string }
  | { type: 'done'; messageId: string }
  | { type: 'error'; detail: string }

export const coachApi = {
  history: (limit = 50) => http.get<ChatMessage[]>(`/chat/history?limit=${limit}`),
  /** The answer as it is written, a fragment at a time. */
  ask: (content: string) => readAnswer(content),
  clear: () => http.delete('/chat/history'),
}

async function* readAnswer(content: string): AsyncGenerator<CoachEvent> {
  for await (const event of streamEvents('/chat', { content })) {
    const payload = JSON.parse(event.data)
    if (event.event === 'delta') yield { type: 'delta', text: payload.text }
    else if (event.event === 'done') yield { type: 'done', messageId: payload.message_id }
    else if (event.event === 'error') yield { type: 'error', detail: payload.detail }
  }
}
