import { useQuery } from '@tanstack/react-query'
import { ErrorNote, Loading, Sheet, Tag } from '../../components/ui'
import { muscleLabel } from '../../constants/muscles'
import { queryKeys } from '../../constants/query-keys'
import { prescriptionCompact } from '../programs/prescription'
import { ApiError } from '../../services/httpClient'
import type { ProgramExercise } from '../../types/api'
import { exercisesApi } from './api'

/**
 * What else could be done instead of this exercise, from the course library.
 *
 * The list is read-only on purpose: swapping an exercise has to change every remaining
 * week of the program, and the backend has no endpoint that does that yet. Rows that
 * looked tappable would promise a swap the app cannot perform.
 */
export function AlternativesSheet({
  exercise,
  onClose,
}: {
  exercise: ProgramExercise | null
  onClose: () => void
}) {
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

  const source = unknownName ? byMuscle : alternatives
  const items = source.data ?? []

  return (
    <Sheet open={!!exercise} onClose={onClose} title={name}>
      {exercise && (
        <p className="num mb-3 text-[13px] text-chalk-500">{prescriptionCompact(exercise)}</p>
      )}

      <p className="label-micro mb-2">
        {unknownName ? `Упражнения за ${muscleLabel(muscle) || 'тази група'}` : 'Алтернативи от курса'}
      </p>

      {unknownName && (
        <p className="mb-3 text-xs leading-relaxed text-chalk-500">
          „{name}“ не е в библиотеката под това име, затова показваме всички упражнения за групата.
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
        <ul className="max-h-[50vh] space-y-2 overflow-y-auto">
          {items.map((item) => (
            <li
              key={item.name}
              className="flex items-center gap-3 rounded-xl border border-ink-700 bg-ink-800 px-4 py-3"
            >
              <span className="min-w-0 flex-1">
                <span className="block truncate text-[15px] font-medium text-chalk-50">
                  {item.name}
                </span>
                <span className="block text-xs text-chalk-500">{item.category}</span>
              </span>
              {item.muscle_group && <Tag>{muscleLabel(item.muscle_group)}</Tag>}
            </li>
          ))}
        </ul>
      )}
    </Sheet>
  )
}
