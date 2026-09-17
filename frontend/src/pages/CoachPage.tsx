import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Screen } from '../components/layout/Screen'
import { ErrorNote, Icon, Loading, Sheet } from '../components/ui'
import { queryKeys } from '../constants/query-keys'
import { coachApi } from '../features/coach/api'
import { ChatBubble, TypingBubble } from '../features/coach/ChatBubble'
import { ChatComposer } from '../features/coach/ChatComposer'

/** Openers for an empty conversation.
 *
 *  Deliberately questions the course answers well - protein, weekly volume, deloads,
 *  plateaus - because an empty chat box invites a question the materials cannot ground,
 *  and the first answer a user ever gets decides whether they ask a second one. */
const SUGGESTIONS = [
  'Колко протеин ми трябва на ден?',
  'Колко серии седмично за гърди?',
  'Кога трябва да направя deload?',
  'Как да пробия застой на лежанка?',
]

export function CoachPage() {
  const queryClient = useQueryClient()
  const endRef = useRef<HTMLDivElement>(null)
  const [clearOpen, setClearOpen] = useState(false)

  const history = useQuery({ queryKey: queryKeys.chat, queryFn: () => coachApi.history() })
  const send = useMutation({
    mutationFn: coachApi.send,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.chat }),
  })
  const clear = useMutation({
    mutationFn: coachApi.clear,
    onSuccess: () => {
      setClearOpen(false)
      queryClient.invalidateQueries({ queryKey: queryKeys.chat })
    },
  })

  const messages = history.data ?? []

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, send.isPending])

  return (
    <Screen title="Треньор" subtitle="Отговорите се основават на курса на Henselmans">
      <div className="flex min-h-[calc(100dvh-13rem)] flex-col">
        {messages.length > 0 && (
          <div className="mb-3 flex justify-end">
            <button
              onClick={() => setClearOpen(true)}
              className="flex items-center gap-1.5 py-1 text-xs font-semibold tracking-wider text-chalk-500 uppercase"
            >
              <Icon name="trash" size={13} />
              Изчисти
            </button>
          </div>
        )}

        <div className="flex-1 space-y-3">
          {history.isLoading && <Loading />}
          {history.error && <ErrorNote error={history.error} onRetry={() => history.refetch()} />}

          {!history.isLoading && !messages.length && (
            <div className="space-y-3">
              <p className="text-sm text-chalk-500">
                Питай за тренировки, хранене или възстановяване. Ето откъде да започнеш:
              </p>
              <div className="grid gap-2">
                {SUGGESTIONS.map((question) => (
                  <button
                    key={question}
                    type="button"
                    onClick={() => send.mutate(question)}
                    disabled={send.isPending}
                    className="min-h-11 rounded-xl border border-ink-700 bg-ink-900 px-4 py-2.5 text-left text-sm text-chalk-300 active:scale-[0.99] disabled:opacity-60"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <ChatBubble key={message.id} message={message} />
          ))}

          {send.isPending && <TypingBubble />}
          {/* The composer is sticky and overlays the end of the list, so the last
              message - citations included - needs room to clear it. */}
          <div ref={endRef} className="h-14" />
        </div>

        <div className="sticky bottom-[4.5rem] mt-4 bg-ink-950 pt-2">
          <ChatComposer onSend={(text) => send.mutate(text)} isPending={send.isPending} />
        </div>
      </div>

      <Sheet open={clearOpen} onClose={() => setClearOpen(false)} title="Изчисти разговора">
        <p className="text-sm text-chalk-300">
          Историята на разговора ще бъде изтрита. Профилът, програмата и тренировките ти остават
          непроменени.
        </p>
        {clear.error && (
          <div className="mt-3">
            <ErrorNote error={clear.error} />
          </div>
        )}
        <div className="mt-4 space-y-2">
          <button
            type="button"
            onClick={() => clear.mutate()}
            disabled={clear.isPending}
            className="btn-danger w-full"
          >
            {clear.isPending ? 'Изтриваме…' : 'Изтрий историята'}
          </button>
          <button type="button" onClick={() => setClearOpen(false)} className="btn-ghost w-full">
            Откажи
          </button>
        </div>
      </Sheet>
    </Screen>
  )
}
