import { useEffect, useRef, useState } from 'react'
import { Screen } from '../components/layout/Screen'
import { ErrorNote, Icon, Loading, Sheet } from '../components/ui'
import { ChatBubble, TypingBubble } from '../features/coach/ChatBubble'
import { ChatComposer } from '../features/coach/ChatComposer'
import { useCoachChat } from '../features/coach/useCoachChat'

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
  const endRef = useRef<HTMLDivElement>(null)
  const [clearOpen, setClearOpen] = useState(false)
  const { history, messages, pending, ask, discard, isAnswering, clear } = useCoachChat()

  useEffect(() => {
    // Smoothly for a new message, instantly while the answer is being written: a smooth
    // scroll restarted on every token never arrives anywhere.
    endRef.current?.scrollIntoView({ behavior: pending?.answer ? 'auto' : 'smooth' })
  }, [messages.length, pending?.question, pending?.answer])

  const isEmpty = !messages.length && !pending

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

          {!history.isLoading && isEmpty && (
            <div className="space-y-3">
              <p className="text-sm text-chalk-500">
                Питай за тренировки, хранене или възстановяване. Ето откъде да започнеш:
              </p>
              <div className="grid gap-2">
                {SUGGESTIONS.map((question) => (
                  <button
                    key={question}
                    type="button"
                    onClick={() => ask(question)}
                    disabled={isAnswering}
                    className="min-h-11 rounded-xl border border-ink-700 bg-ink-900 px-4 py-2.5 text-left text-sm text-chalk-300 active:scale-[0.99] disabled:opacity-60"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <ChatBubble key={message.id} role={message.role} content={message.content} />
          ))}

          {/* The turn in flight. Nothing here is stored yet: on failure the question stays
              on screen so it can be sent again without being typed again. */}
          {pending && (
            <>
              <ChatBubble role="user" content={pending.question} />
              {pending.answer ? (
                <ChatBubble role="assistant" content={pending.answer} />
              ) : (
                !pending.failed && <TypingBubble />
              )}
              {pending.failed && (
                <div className="space-y-2">
                  <ErrorNote error={pending.failed} onRetry={() => ask(pending.question)} />
                  <button type="button" onClick={discard} className="btn-ghost w-full">
                    Откажи въпроса
                  </button>
                </div>
              )}
            </>
          )}

          {/* The composer is sticky and overlays the end of the list, so the last
              message - citations included - needs room to clear it. */}
          <div ref={endRef} className="h-14" />
        </div>

        <div className="sticky bottom-[4.5rem] mt-4 bg-ink-950 pt-2">
          <ChatComposer onSend={ask} isPending={isAnswering} />
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
