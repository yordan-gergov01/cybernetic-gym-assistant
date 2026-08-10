import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { SubPageHeader } from '../components/layout/SubPageHeader'
import { Callout, ErrorNote, Loading, OptionCard, type CalloutTone } from '../components/ui'
import { queryKeys } from '../constants/query-keys'
import { DECISION_LABEL, FATIGUE_QUESTIONS } from '../features/fatigue/constants'
import { programsApi } from '../features/programs/api'
import { workoutsApi } from '../features/workouts/api'
import type { FatigueAnswers, FatigueAssessment } from '../types/api'

const TONE: Record<string, CalloutTone> = { continue: 'ok', caution: 'warn', deload: 'danger' }

/** The weekly recovery check-in: six questions, one screen each.
 *
 *  One question at a time on purpose - a single list of six dropdowns gets answered
 *  carelessly, and every answer here feeds a real deload decision. */
export function CheckInPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<Partial<FatigueAnswers>>({})
  const [result, setResult] = useState<FatigueAssessment | null>(null)

  const today = useQuery({ queryKey: queryKeys.today, queryFn: workoutsApi.today, retry: false })

  const submit = useMutation({
    mutationFn: (complete: FatigueAnswers) =>
      programsApi.submitFatigue(today.data!.program_id, {
        week_number: today.data!.week_number,
        answers: complete,
      }),
    onSuccess: setResult,
  })

  const question = FATIGUE_QUESTIONS[step]

  const answer = (value: string | boolean) => {
    const next = { ...answers, [question.key]: value }
    setAnswers(next)
    if (step + 1 < FATIGUE_QUESTIONS.length) {
      setStep(step + 1)
      return
    }
    submit.mutate(next as FatigueAnswers)
  }

  if (today.isLoading) {
    return (
      <div className="min-h-dvh bg-ink-950">
        <SubPageHeader title="Седмичен чек-ин" />
        <Loading />
      </div>
    )
  }

  if (!today.data) {
    return (
      <div className="min-h-dvh bg-ink-950">
        <SubPageHeader title="Седмичен чек-ин" />
        <main className="mx-auto max-w-lg px-4 pt-6">
          <p className="card text-sm text-chalk-500">
            Чек-инът се прави спрямо активна програма. Създай програма и се върни.
          </p>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-dvh bg-ink-950">
      <SubPageHeader title="Седмичен чек-ин" />

      <main className="mx-auto max-w-lg px-4 pt-4 pb-10">
        {result ? (
          <>
            <Callout
              tone={TONE[result.agent_decision] ?? 'accent'}
              title={DECISION_LABEL[result.agent_decision] ?? result.agent_decision}
            >
              {result.agent_reasoning}
            </Callout>
            <button type="button" onClick={() => navigate('/')} className="btn-primary w-full mt-4">
              Готово
            </button>
          </>
        ) : (
          <>
            <div className="flex gap-1" role="progressbar" aria-valuenow={step + 1} aria-valuemax={FATIGUE_QUESTIONS.length}>
              {FATIGUE_QUESTIONS.map((_, i) => (
                <span
                  key={i}
                  className={`h-1 flex-1 rounded-full ${i <= step ? 'bg-volt-500' : 'bg-ink-700'}`}
                />
              ))}
            </div>

            <p className="label-micro mt-5">
              Въпрос {step + 1} от {FATIGUE_QUESTIONS.length}
            </p>
            <h2 className="mt-2 font-display text-2xl leading-tight font-semibold tracking-wide">
              {question.question}
            </h2>

            <div className="mt-6 space-y-3">
              {question.options.map((option) => (
                <OptionCard
                  key={String(option.value)}
                  option={{ value: String(option.value), label: option.label }}
                  selected={answers[question.key] === option.value}
                  onSelect={() => answer(option.value)}
                />
              ))}
            </div>

            {submit.isPending && <p className="mt-6 text-sm text-chalk-500">Изчисляваме решението…</p>}
            {submit.error && (
              <div className="mt-6">
                <ErrorNote error={submit.error} />
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
