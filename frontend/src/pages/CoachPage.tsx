import { useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Screen } from '../components/layout/Screen'
import { ErrorNote, Loading } from '../components/ui'
import { queryKeys } from '../constants/query-keys'
import { useAuth } from '../features/auth/useAuth'
import { coachApi } from '../features/coach/api'
import { ChatBubble, TypingBubble } from '../features/coach/ChatBubble'
import { ChatComposer } from '../features/coach/ChatComposer'

export function CoachPage() {
  const queryClient = useQueryClient()
  const { logout } = useAuth()
  const endRef = useRef<HTMLDivElement>(null)

  const history = useQuery({ queryKey: queryKeys.chat, queryFn: () => coachApi.history() })
  const send = useMutation({
    mutationFn: coachApi.send,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.chat }),
  })

  const messages = history.data ?? []

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, send.isPending])

  return (
    <Screen title="Треньор" subtitle="Отговорите се основават на курса на Henselmans">
    <div className="flex min-h-[calc(100dvh-13rem)] flex-col">
      <div className="mb-3 flex justify-end">
        <button onClick={logout} className="tap py-1 text-xs font-semibold tracking-wider text-chalk-500 uppercase">
          Изход
        </button>
      </div>

      <div className="flex-1 space-y-3">
        {history.isLoading && <Loading />}
        {history.error && <ErrorNote error={history.error} onRetry={() => history.refetch()} />}

        {!history.isLoading && !messages.length && (
          <div className="card text-center text-sm text-chalk-500">
            Питай за тренировки, хранене или възстановяване.
          </div>
        )}

        {messages.map((message) => (
          <ChatBubble key={message.id} message={message} />
        ))}

        {send.isPending && <TypingBubble />}
        <div ref={endRef} />
      </div>

      <div className="sticky bottom-[4.5rem] mt-4 bg-ink-950 pt-2">
        <ChatComposer onSend={(text) => send.mutate(text)} isPending={send.isPending} />
      </div>
    </div>
    </Screen>
  )
}
