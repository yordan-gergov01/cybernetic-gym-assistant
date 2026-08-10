import { ErrorNote } from '../../components/ui'
import { ExerciseCard } from './ExerciseCard'
import { useWorkoutLogger } from './useWorkoutLogger'
import type { ProgramExercise } from '../../types/api'

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

  return (
    <>
      <div className="space-y-3">
        {exercises.map((exercise) => (
          <ExerciseCard
            key={exercise.id}
            exercise={exercise}
            rows={logger.rowsFor(exercise)}
            onChangeRow={(index, patch) => logger.updateRow(exercise, index, patch)}
          />
        ))}
      </div>

      {logger.saveError && (
        <div className="mt-4">
          <ErrorNote error={logger.saveError} />
        </div>
      )}

      {logger.completedCount > 0 && (
        <div className="fixed inset-x-0 bottom-[3.5rem] z-20 bg-gradient-to-t from-ink-950 via-ink-950/95 to-transparent pt-6">
          <div className="safe-bottom mx-auto max-w-lg px-4 pb-3">
            <button
              onClick={logger.finish}
              disabled={logger.isSaving}
              className="btn-primary w-full shadow-xl shadow-ink-950/80"
            >
              {logger.isSaving ? 'Записване…' : `Завърши тренировката · ${logger.completedCount}`}
            </button>
          </div>
        </div>
      )}
    </>
  )
}
