import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Callout, ErrorNote, Loading, Sheet, Tag } from '../../components/ui'
import { muscleLabel } from '../../constants/muscles'
import { queryKeys } from '../../constants/query-keys'
import { prescriptionCompact } from '../programs/prescription'
import { programsApi } from '../programs/api'
import { ApiError } from '../../services/httpClient'
import type { ProgramExercise } from '../../types/api'
import { exercisesApi } from './api'

/**
 * What else could be done instead of this exercise, and the swap itself.
 *
 * Picking an alternative rewrites the exercise in every week of the program, so it is
 * confirmed rather than applied on a single tap - a mis-tap here changes the whole plan.
 */
export function AlternativesSheet({
  programId,
  exercise,
  onClose,
}: {
  programId: string
  exercise: ProgramExercise | null
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const [picked, setPicked] = useState<string | null>(null)

  const name = exercise?.exercise_name ?? ''
  const muscle = exercise?.muscle_group ?? ''

  const alternatives = useQuery({
    queryKey: queryKeys.exerciseAlternatives(name),
    queryFn: () => exercisesApi.alternatives(name),
    enabled: !!exercise,
    retry: false,
  })

  // The library is keyed by the guide's own names ("Barbell overhead press"), while a
  // program is written in standard gym names, so an exact match often fails. Falling
  // back to the muscle group keeps the answer useful and says why it is broader.
  const unknownName = alternatives.error instanceof ApiError && alternatives.error.status === 404
  const byMuscle = useQuery({
    queryKey: queryKeys.exercises(`muscle:${muscle}`),
    queryFn: () => exercisesApi.list({ muscle_group: muscle }),
    enabled: !!exercise && unknownName && !!muscle,
  })

  const swap = useMutation({
    mutationFn: (replacement: string) =>
      programsApi.swapExercise(programId, { exercise_name: name, replacement_name: replacement }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.program(programId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.programReview(programId) })
      // The swapped exercise is prescribed for today's session as well.
      queryClient.invalidateQueries({ queryKey: queryKeys.today })
    },
  })

  const close = () => {
    setPicked(null)
    swap.reset()
    onClose()
  }

  const source = unknownName ? byMuscle : alternatives
  const items = source.data ?? []

  return (
    <Sheet open={!!exercise} onClose={close} title={name}>
      {swap.data ? (
        <>
          <Callout tone="ok" title="Програмата е обновена">
            {swap.data.summary_bg}
          </Callout>
          <button type="button" onClick={close} className="btn-primary mt-3 w-full">
            Готово
          </button>
        </>
      ) : (
        <>
          {exercise && (
            <p className="num mb-3 text-[13px] text-chalk-500">{prescriptionCompact(exercise)}</p>
          )}

          <p className="label-micro mb-2">
            {unknownName
              ? `Упражнения за ${muscleLabel(muscle) || 'тази група'}`
              : 'Алтернативи от курса'}
          </p>

          {unknownName && (
            <p className="mb-3 text-xs leading-relaxed text-chalk-500">
              „{name}“ не е в библиотеката под това име, затова показваме всички упражнения за
              групата.
            </p>
          )}

          {source.isLoading ? (
            <Loading />
          ) : source.error && !unknownName ? (
            <ErrorNote error={source.error} onRetry={() => source.refetch()} />
          ) : !items.length ? (
            <p className="text-sm text-chalk-500">
              Няма алтернативи в библиотеката на курса за това движение.
            </p>
          ) : (
            <ul className="max-h-[45vh] space-y-2 overflow-y-auto">
              {items.map((item) => (
                <li key={item.name}>
                  <button
                    type="button"
                    onClick={() => setPicked(item.name)}
                    aria-pressed={picked === item.name}
                    className={`tap flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left ${
                      picked === item.name
                        ? 'border-volt-500 bg-volt-500/8'
                        : 'border-ink-700 bg-ink-800'
                    }`}
                  >
                    <span className="min-w-0 flex-1">
                      <span
                        className={`block truncate text-[15px] font-medium ${
                          picked === item.name ? 'text-volt-400' : 'text-chalk-50'
                        }`}
                      >
                        {item.name}
                      </span>
                      <span className="block text-xs text-chalk-500">{item.category}</span>
                    </span>
                    {item.muscle_group && <Tag>{muscleLabel(item.muscle_group)}</Tag>}
                  </button>
                </li>
              ))}
            </ul>
          )}

          {swap.error && (
            <div className="mt-3">
              <ErrorNote error={swap.error} />
            </div>
          )}

          {picked && (
            <div className="mt-3 border-t border-ink-700 pt-3">
              <p className="mb-2 text-sm text-chalk-300">
                „{name}“ се заменя с „{picked}“ във всички седмици на програмата.
              </p>
              <button
                type="button"
                onClick={() => swap.mutate(picked)}
                disabled={swap.isPending}
                className="btn-primary w-full"
              >
                {swap.isPending ? 'Заменям…' : 'Замени упражнението'}
              </button>
              <button type="button" onClick={() => setPicked(null)} className="btn-ghost mt-2 w-full">
                Откажи
              </button>
            </div>
          )}
        </>
      )}
    </Sheet>
  )
}
