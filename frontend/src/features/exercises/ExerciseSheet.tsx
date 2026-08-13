import { Sheet, Tag } from '../../components/ui'
import { muscleLabel } from '../../constants/muscles'
import type { Exercise } from '../../types/api'

/** One library entry: where the guide files it, and its technique cues verbatim.
 *
 *  The cues are the reason the library is in the app at all - a name alone is something
 *  the user already knows. */
export function ExerciseSheet({
  exercise,
  onClose,
}: {
  exercise: Exercise | null
  onClose: () => void
}) {
  return (
    <Sheet open={!!exercise} onClose={onClose} title={exercise?.name}>
      {exercise && (
        <>
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <Tag>{exercise.category}</Tag>
            {exercise.muscle_group && <Tag>{muscleLabel(exercise.muscle_group)}</Tag>}
          </div>

          {exercise.cues.length ? (
            <ul className="max-h-[50vh] space-y-2 overflow-y-auto">
              {exercise.cues.map((cue) => (
                <li key={cue} className="flex gap-3 text-sm leading-relaxed text-chalk-300">
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-volt-500" />
                  <span>{cue}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-chalk-500">Ръководството не дава насоки за това упражнение.</p>
          )}
        </>
      )}
    </Sheet>
  )
}
