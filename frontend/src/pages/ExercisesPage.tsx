import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { SubPageHeader } from '../components/layout/SubPageHeader'
import { Chip, EmptyState, ErrorNote, Icon, ListRow, Loading, Tag } from '../components/ui'
import { muscleLabel } from '../constants/muscles'
import { queryKeys } from '../constants/query-keys'
import { exercisesApi } from '../features/exercises/api'
import { ExerciseSheet } from '../features/exercises/ExerciseSheet'
import type { Exercise } from '../types/api'

/**
 * The course exercise library: what the guide files under each movement pattern, and
 * the technique cues for one exercise.
 *
 * Opened from the program screen with `?muscle=` when a stalled lift needs replacing.
 * Only one filter is applied at a time, because the API resolves category before
 * muscle group - showing both as active would claim a filter that never ran.
 */
export function ExercisesPage() {
  const [params, setParams] = useSearchParams()
  const muscle = params.get('muscle') ?? ''

  const [category, setCategory] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<Exercise | null>(null)

  const categories = useQuery({
    queryKey: queryKeys.exerciseCategories,
    queryFn: exercisesApi.categories,
    enabled: !muscle,
  })

  const filter = muscle ? { muscle_group: muscle } : { category: category ?? undefined }
  const exercises = useQuery({
    queryKey: queryKeys.exercises(muscle ? `muscle:${muscle}` : `category:${category ?? 'all'}`),
    queryFn: () => exercisesApi.list(filter),
  })

  const needle = search.trim().toLowerCase()
  const items = (exercises.data ?? []).filter((item) => item.name.toLowerCase().includes(needle))

  return (
    <div className="min-h-dvh bg-ink-950">
      <SubPageHeader
        title="Упражнения"
        subtitle={muscle ? `Само за ${muscleLabel(muscle)}` : undefined}
      />

      <main className="mx-auto max-w-lg px-4 pt-4 pb-12">
        <div className="relative">
          <Icon
            name="search"
            size={18}
            className="pointer-events-none absolute top-1/2 left-4 -translate-y-1/2 text-chalk-500"
          />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Търси упражнение"
            aria-label="Търси упражнение"
            className="input pl-11"
          />
        </div>

        {muscle ? (
          <button
            type="button"
            onClick={() => {
              setParams({})
              setCategory(null)
            }}
            className="btn-ghost mt-3 w-full"
          >
            Покажи всички упражнения
          </button>
        ) : (
          <div className="no-scrollbar -mx-4 mt-3 flex gap-2 overflow-x-auto px-4">
            <Chip label="Всички" selected={category === null} onToggle={() => setCategory(null)} />
            {(categories.data ?? []).map((name) => (
              <Chip
                key={name}
                label={name}
                selected={category === name}
                onToggle={() => setCategory(category === name ? null : name)}
              />
            ))}
          </div>
        )}

        <div className="mt-4">
          {exercises.isLoading ? (
            <Loading />
          ) : exercises.error ? (
            <ErrorNote error={exercises.error} onRetry={() => exercises.refetch()} />
          ) : !items.length ? (
            <EmptyState
              title="Няма съвпадение"
              hint="Имената в библиотеката са тези от ръководството на курса - опитай с по-кратка дума."
            />
          ) : (
            <div className="space-y-2">
              {items.map((exercise) => (
                <ListRow
                  key={exercise.name}
                  title={exercise.name}
                  subtitle={exercise.category}
                  trailing={
                    exercise.muscle_group ? <Tag>{muscleLabel(exercise.muscle_group)}</Tag> : undefined
                  }
                  onClick={() => setSelected(exercise)}
                  chevron
                />
              ))}
            </div>
          )}
        </div>
      </main>

      <ExerciseSheet exercise={selected} onClose={() => setSelected(null)} />
    </div>
  )
}
