import { Screen } from '../components/layout/Screen'
import { EmptyState, ErrorNote, Icon, Loading } from '../components/ui'
import { StartProgramCard } from '../features/programs/StartProgramCard'
import { ExerciseCard } from '../features/workouts/ExerciseCard'
import { useTodayWorkout } from '../features/workouts/useTodayWorkout'
import { WeekStrip, type DayStatus } from '../features/workouts/WeekStrip'
import { formatDayLabel, todayIso } from '../utils/date'

const HEADER_ACTIONS = [
  { to: '/program', icon: 'calendar' as const, label: 'Програма' },
  { to: '/notifications', icon: 'bell' as const, label: 'Известия' },
]

export function TodayPage() {
  const workout = useTodayWorkout()

  // Until day-by-calendar lands, mark the weekday we are on and leave the rest neutral.
  const weekday = (new Date().getDay() + 6) % 7
  const statuses: DayStatus[] = Array.from({ length: 7 }, (_, i) => (i === weekday ? 'today' : 'upcoming'))

  if (workout.isLoading) {
    return (
      <Screen title="Днес" subtitle={formatDayLabel(todayIso())} actions={HEADER_ACTIONS}>
        <Loading />
      </Screen>
    )
  }

  if (workout.error) {
    return (
      <Screen title="Днес" actions={HEADER_ACTIONS}>
        <ErrorNote error={workout.error} onRetry={workout.refetch} />
      </Screen>
    )
  }

  if (!workout.hasProgram) {
    return (
      <Screen title="Днес" subtitle={formatDayLabel(todayIso())} actions={HEADER_ACTIONS}>
        <WeekStrip statuses={statuses} />
        <StartProgramCard />
      </Screen>
    )
  }

  if (!workout.day) {
    return (
      <Screen title="Почивен ден" subtitle={formatDayLabel(todayIso())} actions={HEADER_ACTIONS}>
        <WeekStrip statuses={statuses} />
        <EmptyState title="Почивен ден" hint="Възстановяването е част от програмата." />
      </Screen>
    )
  }

  const exercises = [...workout.day.exercises].sort((a, b) => a.order_index - b.order_index)
  const totalSets = exercises.reduce((sum, ex) => sum + (ex.sets_prescribed ?? 3), 0)

  return (
    <Screen
      title={workout.day.day_name || `Ден ${workout.day.day_number}`}
      subtitle={workout.programName}
      actions={HEADER_ACTIONS}
    >
      <WeekStrip statuses={statuses} />

      {/* Session summary - the "what am I in for" glance before starting. */}
      <section className="card mb-4">
        <p className="mb-3 text-[10px] font-semibold tracking-[0.12em] text-chalk-500 uppercase">
          Днешната сесия
        </p>
        <div className="flex items-center gap-4 text-sm text-chalk-300">
          <span className="flex items-center gap-1.5">
            <Icon name="dumbbell" size={16} className="text-chalk-500" />
            <span className="num text-chalk-50">{exercises.length}</span> упражнения
          </span>
          <span className="flex items-center gap-1.5">
            <Icon name="target" size={16} className="text-chalk-500" />
            <span className="num text-chalk-50">~{totalSets}</span> серии
          </span>
        </div>
      </section>

      <div className="space-y-3">
        {exercises.map((exercise) => (
          <ExerciseCard
            key={exercise.id}
            exercise={exercise}
            rows={workout.rowsFor(exercise)}
            onChangeRow={(index, patch) => workout.updateRow(exercise, index, patch)}
          />
        ))}
      </div>

      {workout.saveError && (
        <div className="mt-4">
          <ErrorNote error={workout.saveError} />
        </div>
      )}

      {/* Only appears once something is logged: a disabled floating button is
          translucent, so it just smears over the exercise underneath it. The gradient
          strip keeps the content readable as it scrolls behind. */}
      {workout.completedCount > 0 && (
        <div className="fixed inset-x-0 bottom-[3.5rem] z-20 bg-gradient-to-t from-ink-950 via-ink-950/95 to-transparent pt-6">
          <div className="safe-bottom mx-auto max-w-lg px-4 pb-3">
            <button
              onClick={workout.finish}
              disabled={workout.isSaving}
              className="btn-primary w-full shadow-xl shadow-ink-950/80"
            >
              {workout.isSaving ? 'Записване…' : `Завърши тренировката · ${workout.completedCount}`}
            </button>
          </div>
        </div>
      )}
    </Screen>
  )
}
