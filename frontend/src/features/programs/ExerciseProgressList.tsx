import { ListRow, Tag } from '../../components/ui'
import { muscleLabel } from '../../constants/muscles'
import type { ExerciseProgress, PlateauBreaker } from '../../types/api'
import { formatWeight } from '../../utils/format'

const STATUS: Record<ExerciseProgress['status'], { label: string; className: string }> = {
  stalled: { label: 'Застой', className: 'text-danger-400' },
  holding: { label: 'Задържа', className: 'text-warn-400' },
  progressing: { label: 'Прогрес', className: 'text-ok-400' },
  insufficient_data: { label: 'Малко данни', className: 'text-chalk-500' },
}

/** Worst first: a stalled lift is the reason to open this screen, and it must not sit
 *  below ten exercises that are fine. */
const ORDER: ExerciseProgress['status'][] = ['stalled', 'holding', 'progressing', 'insufficient_data']

/**
 * Per-exercise progress from the program review.
 *
 * The plateau-breaker weight is shown on the row of the exercise it belongs to rather
 * than in a list of its own - it is the answer to that one exercise holding still, and
 * separating them would make the user match names by hand.
 */
export function ExerciseProgressList({
  exercises,
  breakers,
  skipped,
}: {
  exercises: ExerciseProgress[]
  breakers: PlateauBreaker[]
  skipped: string[]
}) {
  const breakerFor = new Map(breakers.map((breaker) => [breaker.exercise_name, breaker]))
  const sorted = [...exercises].sort(
    (a, b) => ORDER.indexOf(a.status) - ORDER.indexOf(b.status),
  )

  return (
    <div className="space-y-2">
      {sorted.map((exercise) => {
        const status = STATUS[exercise.status]
        const breaker = breakerFor.get(exercise.exercise_name)
        const details = [
          muscleLabel(exercise.muscle_group),
          exercise.best_e1rm ? `e1RM ${formatWeight(exercise.best_e1rm)} кг` : null,
          exercise.change_pct !== null && exercise.change_pct !== undefined
            ? `${exercise.change_pct > 0 ? '+' : ''}${exercise.change_pct}%`
            : null,
        ]
          .filter(Boolean)
          .join(' · ')

        return (
          <ListRow
            key={exercise.exercise_name}
            title={exercise.exercise_name}
            subtitle={
              <>
                <span className="block">{details}</span>
                {breaker && (
                  <span className="block text-volt-400">
                    Пробив: {formatWeight(breaker.weight_kg)} кг × {breaker.reps}
                  </span>
                )}
              </>
            }
            trailing={<Tag className={status.className}>{status.label}</Tag>}
          />
        )
      })}

      {skipped.length > 0 && (
        <p className="px-1 pt-1 text-xs leading-relaxed text-chalk-500">
          Без логнати работни серии, затова не са оценени: {skipped.join(', ')}.
        </p>
      )}
    </div>
  )
}
