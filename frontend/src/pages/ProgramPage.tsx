import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { SubPageHeader } from '../components/layout/SubPageHeader'
import { ErrorNote, Icon, ListRow, Loading, SectionHeader, Sheet } from '../components/ui'
import { goalLabel } from '../constants/goals'
import { queryKeys } from '../constants/query-keys'
import { AlternativesSheet } from '../features/exercises/AlternativesSheet'
import { programsApi } from '../features/programs/api'
import { ExerciseProgressList } from '../features/programs/ExerciseProgressList'
import { prescriptionCompact } from '../features/programs/prescription'
import { ReviewCard } from '../features/programs/ReviewCard'
import { StartProgramCard } from '../features/programs/StartProgramCard'
import { WeekAccordion } from '../features/programs/WeekAccordion'
import { workoutsApi } from '../features/workouts/api'
import { useToday } from '../features/workouts/useWorkoutLogger'
import type { ProgramDay, ProgramExercise, ProgramWeek } from '../types/api'

/** How far back the logged-sessions lookup reaches. A program is capped at 20 weeks, so
 *  200 sessions covers a whole program at any realistic frequency; only how many of them
 *  belong to this program is read. */
const LOG_WINDOW = 200

/** Sessions per week, from the plan itself - the program carries no such field, and a
 *  number that disagreed with the days listed below it would be worse than none. */
const daysPerWeek = (weeks: ProgramWeek[]): number => {
  const first = [...weeks].sort((a, b) => a.week_number - b.week_number)[0]
  return first ? first.days.filter((day) => !day.is_rest_day).length : 0
}

/** The active program, or the most recent one when everything is archived. */
export function ProgramPage() {
  const programs = useQuery({ queryKey: queryKeys.programs, queryFn: programsApi.list })
  const program = programs.data?.find((p) => p.status === 'active') ?? programs.data?.[0]

  if (programs.isLoading || programs.error || !program) {
    return (
      <div className="min-h-dvh bg-ink-950">
        <SubPageHeader title="Програма" />
        <main className="mx-auto max-w-lg px-4 pt-4 pb-12">
          {programs.isLoading ? (
            <Loading />
          ) : programs.error ? (
            <ErrorNote error={programs.error} onRetry={() => programs.refetch()} />
          ) : (
            <StartProgramCard />
          )}
        </main>
      </div>
    )
  }

  return <ProgramDetail programId={program.id} />
}

function ProgramDetail({ programId }: { programId: string }) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const program = useQuery({
    queryKey: queryKeys.program(programId),
    queryFn: () => programsApi.get(programId),
  })
  const review = useQuery({
    queryKey: queryKeys.programReview(programId),
    queryFn: () => programsApi.review(programId),
  })
  const logs = useQuery({
    queryKey: queryKeys.workoutLogs(LOG_WINDOW),
    queryFn: () => workoutsApi.list(LOG_WINDOW),
  })
  const today = useToday()

  // `undefined` means "nobody has touched the accordion", so the current week can open
  // itself; `null` is a week the user deliberately collapsed.
  const [openWeek, setOpenWeek] = useState<number | null | undefined>(undefined)
  const [openDay, setOpenDay] = useState<ProgramDay | null>(null)
  const [openExercise, setOpenExercise] = useState<ProgramExercise | null>(null)
  const [confirmArchive, setConfirmArchive] = useState(false)

  const archive = useMutation({
    mutationFn: () => programsApi.archive(programId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.programs })
      queryClient.invalidateQueries({ queryKey: queryKeys.program(programId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.today })
      // Today is where the next step lives once there is no active program.
      navigate('/')
    },
  })

  if (program.isLoading) {
    return (
      <div className="min-h-dvh bg-ink-950">
        <SubPageHeader title="Програма" />
        <main className="mx-auto max-w-lg px-4 pt-4 pb-12">
          <Loading />
        </main>
      </div>
    )
  }

  if (program.error || !program.data) {
    return (
      <div className="min-h-dvh bg-ink-950">
        <SubPageHeader title="Програма" />
        <main className="mx-auto max-w-lg px-4 pt-4 pb-12">
          <ErrorNote error={program.error} onRetry={() => program.refetch()} />
        </main>
      </div>
    )
  }

  const plan = program.data
  const perWeek = daysPerWeek(plan.weeks)
  const subtitle = [
    `${plan.total_weeks} седмици`,
    perWeek ? `${perWeek} дни/седмица` : null,
    plan.goal ? `Цел: ${goalLabel(plan.goal)}` : null,
  ]
    .filter(Boolean)
    .join(' · ')

  // Today only describes the program it belongs to; an archived plan gets no "Днес".
  const isCurrent = today.data?.program_id === plan.id
  const currentWeek = isCurrent ? (today.data?.week_number ?? null) : null
  const shownWeek = openWeek === undefined ? (currentWeek ?? 1) : openWeek

  // A program is a rotation, not a calendar: the backend always serves the first week's
  // days and advances one slot per logged session (services/training_week.py), so every
  // logged session sits on a week-1 day row no matter which week it happened in. That
  // makes the session count - not the day id - what says how far the plan has been run.
  const sessionsDone = (logs.data ?? []).filter((log) => log.program_id === plan.id).length
  const dayStatus = (weekNumber: number, slot: number) => {
    const position = (weekNumber - 1) * perWeek + slot
    if (position < sessionsDone) return 'done'
    if (isCurrent && !today.data?.is_rest_day && position === sessionsDone) return 'today'
    return 'upcoming'
  }

  return (
    <div className="min-h-dvh bg-ink-950">
      <SubPageHeader title={plan.name} subtitle={subtitle} />

      <main className="mx-auto max-w-lg px-4 pt-4 pb-12">
        {review.isLoading ? (
          <Loading />
        ) : review.error ? (
          <ErrorNote error={review.error} onRetry={() => review.refetch()} />
        ) : (
          review.data && <ReviewCard programId={plan.id} review={review.data} />
        )}

        {review.data && review.data.exercises.length > 0 && (
          <>
            <SectionHeader title="Прогрес по упражнения" />
            <ExerciseProgressList
              exercises={review.data.exercises}
              breakers={review.data.breakers}
              skipped={review.data.skipped_exercises}
            />
          </>
        )}

        <SectionHeader title="Седмици" />
        <WeekAccordion
          weeks={plan.weeks}
          openWeek={shownWeek}
          onToggleWeek={(weekNumber) => setOpenWeek(shownWeek === weekNumber ? null : weekNumber)}
          dayStatus={dayStatus}
          onOpenDay={setOpenDay}
        />

        <div className="mt-4">
          <ListRow
            to="/exercises"
            leading={<Icon name="dumbbell" size={18} />}
            title="Библиотека с упражнения"
            subtitle="Упражненията от курса, групирани по движение"
            chevron
          />
        </div>

        {plan.status === 'active' && (
          <div className="mt-8">
            {archive.error && (
              <div className="mb-3">
                <ErrorNote error={archive.error} />
              </div>
            )}
            {confirmArchive ? (
              <div className="space-y-2">
                <p className="text-sm text-chalk-300">
                  Програмата спира, но остава записана заедно с логнатите тренировки.
                </p>
                <button
                  type="button"
                  onClick={() => archive.mutate()}
                  disabled={archive.isPending}
                  className="btn-danger w-full"
                >
                  {archive.isPending ? 'Архивирам…' : 'Да, архивирай'}
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmArchive(false)}
                  className="btn-ghost w-full"
                >
                  Откажи
                </button>
              </div>
            ) : (
              <button type="button" onClick={() => setConfirmArchive(true)} className="btn-ghost w-full">
                Архивирай програмата
              </button>
            )}
          </div>
        )}
      </main>

      <Sheet
        open={!!openDay}
        onClose={() => setOpenDay(null)}
        title={openDay?.day_name || 'Тренировка'}
      >
        <div className="max-h-[60vh] space-y-2 overflow-y-auto">
          {[...(openDay?.exercises ?? [])]
            .sort((a, b) => a.order_index - b.order_index)
            .map((exercise) => (
              <button
                key={exercise.id}
                type="button"
                onClick={() => setOpenExercise(exercise)}
                className="tap flex w-full items-center gap-3 rounded-xl border border-ink-700 bg-ink-800 p-3.5 text-left"
              >
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[15px] font-semibold text-chalk-50">
                    {exercise.exercise_name}
                  </span>
                  <span className="num block text-[13px] text-chalk-500">
                    {prescriptionCompact(exercise)}
                  </span>
                </span>
                <Icon name="chevronRight" size={18} className="shrink-0 text-chalk-500" />
              </button>
            ))}
        </div>
      </Sheet>

      <AlternativesSheet exercise={openExercise} onClose={() => setOpenExercise(null)} />
    </div>
  )
}
