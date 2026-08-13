import { useState } from 'react'
import { Screen } from '../components/layout/Screen'
import { splitLabel } from '../constants/navigation'
import { ErrorNote, ListRow, Loading, SectionHeader, Tag } from '../components/ui'
import { muscleLabel } from '../constants/muscles'
import { prescriptionLong } from '../features/programs/prescription'
import { StartProgramCard } from '../features/programs/StartProgramCard'
import { ActiveSession } from '../features/workouts/ActiveSession'
import { RestDay } from '../features/workouts/RestDay'
import { SessionCard } from '../features/workouts/SessionCard'
import { useToday } from '../features/workouts/useWorkoutLogger'
import { WeekStrip } from '../features/workouts/WeekStrip'
import { ApiError } from '../services/httpClient'

const HEADER_ACTIONS = [
  { to: '/program', icon: 'calendar' as const, label: 'Програма' },
  { to: '/notifications', icon: 'bell' as const, label: 'Известия' },
  { to: '/profile', icon: 'settings' as const, label: 'Профил' },
]

export function TodayPage() {
  const today = useToday()
  const [started, setStarted] = useState(false)

  if (today.isLoading) {
    return (
      <Screen title="Днес" actions={HEADER_ACTIONS}>
        <Loading />
      </Screen>
    )
  }

  // 404 is the honest answer for "no program yet", not an error to apologise for.
  if (today.error instanceof ApiError && today.error.status === 404) {
    return (
      <Screen title="Днес" actions={HEADER_ACTIONS}>
        <StartProgramCard />
      </Screen>
    )
  }

  if (today.error || !today.data) {
    return (
      <Screen title="Днес" actions={HEADER_ACTIONS}>
        <ErrorNote error={today.error} onRetry={today.refetch} />
      </Screen>
    )
  }

  const view = today.data
  const subtitle = [splitLabel(view.template_type), `Седмица ${view.week_number} от ${view.total_weeks}`]
    .filter(Boolean)
    .join(' · ')
  const sessionTitle = view.day_name || 'Днешната тренировка'

  if (view.is_rest_day) {
    return (
      <Screen title="Почивен ден" subtitle={subtitle} actions={HEADER_ACTIONS}>
        <WeekStrip days={view.calendar} />
        <div className="mt-4">
          <RestDay today={view} needsWeighIn={!view.weighed_in_today} />
        </div>
      </Screen>
    )
  }

  return (
    <Screen title={sessionTitle} subtitle={subtitle} actions={HEADER_ACTIONS}>
      <WeekStrip days={view.calendar} />

      <div className="mt-4">
        {started && view.day_id ? (
          <ActiveSession programId={view.program_id} dayId={view.day_id} exercises={view.exercises} />
        ) : (
          <>
            <SessionCard
              title={sessionTitle}
              estimate={view.estimate}
              onStart={() => setStarted(true)}
            />

            <SectionHeader title="Упражнения" />
            <div className="space-y-2">
              {view.exercises.map((exercise, index) => (
                <ListRow
                  key={exercise.id}
                  leading={<span className="num text-sm">{index + 1}</span>}
                  title={exercise.exercise_name}
                  subtitle={prescriptionLong(exercise)}
                  trailing={
                    exercise.muscle_group ? <Tag>{muscleLabel(exercise.muscle_group)}</Tag> : undefined
                  }
                />
              ))}
            </div>
          </>
        )}
      </div>
    </Screen>
  )
}
