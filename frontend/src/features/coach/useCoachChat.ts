import { useCallback, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '../../constants/query-keys'
import { coachApi } from './api'

/** The turn being answered right now: on screen, but not in the history yet.
 *
 *  The question belongs here from the moment it is sent. Drawing the screen from the
 *  history alone meant it appeared only once the whole answer had been generated, so for
 *  several seconds the user saw an empty box and no sign the send had registered. */
export type PendingTurn = { question: string; answer: string; failed: Error | null }

/** The stream ended without saying how it ended. Nothing was stored, so the turn has to
 *  be reported as lost rather than left spinning. */
const INCOMPLETE = 'Връзката прекъсна, преди отговорът да завърши. Опитай пак.'

export function useCoachChat() {
  const queryClient = useQueryClient()
  const history = useQuery({ queryKey: queryKeys.chat, queryFn: () => coachApi.history() })
  const [pending, setPending] = useState<PendingTurn | null>(null)
  // A second question sent mid-answer would interleave two streams into one bubble.
  const answering = useRef(false)

  const ask = useCallback(
    async (question: string) => {
      if (answering.current) return
      answering.current = true
      setPending({ question, answer: '', failed: null })
      try {
        let ended = false
        for await (const event of coachApi.ask(question)) {
          if (event.type === 'delta') {
            setPending((turn) => (turn ? { ...turn, answer: turn.answer + event.text } : turn))
          } else if (event.type === 'error') {
            ended = true
            setPending((turn) => (turn ? { ...turn, failed: new Error(event.detail) } : turn))
          } else {
            ended = true
            // The stored pair has to replace the streamed text within one render, or the
            // answer blinks: once as the fragments, once as the message that came back.
            const stored = await coachApi.history()
            queryClient.setQueryData(queryKeys.chat, stored)
            setPending(null)
          }
        }
        if (!ended) throw new Error(INCOMPLETE)
      } catch (error) {
        const failed = error instanceof Error ? error : new Error(INCOMPLETE)
        setPending((turn) => (turn ? { ...turn, failed } : turn))
      } finally {
        answering.current = false
      }
    },
    [queryClient],
  )

  const clear = useMutation({
    mutationFn: coachApi.clear,
    onSuccess: () => {
      setPending(null)
      return queryClient.invalidateQueries({ queryKey: queryKeys.chat })
    },
  })

  return {
    history,
    messages: history.data ?? [],
    pending,
    ask,
    /** Drop a question the coach never answered, without asking it again. */
    discard: () => setPending(null),
    isAnswering: pending !== null && pending.failed === null,
    clear,
  }
}
