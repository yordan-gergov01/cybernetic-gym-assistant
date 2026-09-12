import { ErrorNote, Icon, Meter } from '../../components/ui'
import { ExerciseCard } from './ExerciseCard'
import { RestTimerBar } from './RestTimerBar'
import { formatClock } from '../../utils/format'
import { useElapsedSeconds, useRestTimer } from './useRestTimer'
import { useWorkoutLogger } from './useWorkoutLogger'
import type { ProgramExercise } from '../../types/api'

/** What the backend falls back to when a program prescribes no rest for an exercise
 *  (domain/schedule.py). Repeated rather than guessed: the two must agree, or the timer
 *  runs for a different interval than the session length the card promised. */
const DEFAULT_REST_SECONDS = 120

/** The session in progress: one card per exercise, with the sets to confirm.
 *
 *  The finish button only appears once something is logged. A disabled floating button
 *  is translucent, so it smears over the exercise underneath it and looks broken. */
export function ActiveSession({
  programId,
  dayId,
  exercises,
}: {
  programId: string
  dayId: string
  exercises: ProgramExercise[]
}) {
  const logger = useWorkoutLogger({ programId, dayId, exercises })
  const rest = useRestTimer()
  const elapsed = useElapsedSeconds()

  return (
    <>
      <div className="mb-3 flex items-center gap-3 rounded-xl border border-ink-700 bg-ink-900/60 px-3 py-2">
        <Icon name="timer" size={16} className="shrink-0 text-chalk-500" />
        <span className="shrink-0 font-display text-base font-semibold tabular-nums text-chalk-50">
          {formatClock(elapsed)}
        </span>
        <div className="min-w-0 flex-1">
          <Meter value={logger.completedCount} max={logger.plannedCount} />
        </div>
        <span className="shrink-0 text-xs tabular-nums text-chalk-500">
          {logger.completedCount}/{logger.plannedCount} серии
        </span>
      </div>

      <div className="space-y-3">
        {exercises.map((exercise) => (
          <ExerciseCard
            key={exercise.id}
            exercise={exercise}
            rows={logger.rowsFor(exercise)}
            onChangeRow={(index, patch) => {
              logger.updateRow(exercise, index, patch)
              // Only a set being ticked starts the rest; unticking a mistake must not.
              if (patch.done) rest.start(exercise.rest_seconds ?? DEFAULT_REST_SECONDS)
            }}
            onAddRow={() => logger.addRow(exercise)}
          />
        ))}
      </div>

      {logger.saveError && (
        <div className="mt-4">
          <ErrorNote error={logger.saveError} />
        </div>
      )}

      {(rest.remaining !== null || logger.completedCount > 0) && (
        <div className="fixed inset-x-0 bottom-[3.5rem] z-20 bg-gradient-to-t from-ink-950 via-ink-950/95 to-transparent pt-6">
          <div className="safe-bottom mx-auto max-w-lg space-y-2 px-4 pb-3">
            {rest.remaining !== null && (
              <RestTimerBar
                remaining={rest.remaining}
                total={rest.total}
                onExtend={rest.extend}
                onSkip={rest.skip}
              />
            )}

            {logger.completedCount > 0 && (
              <button
                onClick={logger.finish}
                disabled={logger.isSaving}
                className="btn-primary w-full shadow-xl shadow-ink-950/80"
              >
                {logger.isSaving ? 'Записване…' : `Завърши тренировката · ${logger.completedCount}`}
              </button>
            )}
          </div>
        </div>
      )}
    </>
  )
}
