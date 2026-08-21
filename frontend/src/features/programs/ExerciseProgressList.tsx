import { ListRow, Tag } from '../../components/ui'
import { muscleLabel } from '../../constants/muscles'
import type { ExerciseProgress, ExerciseTechnique } from '../../types/api'
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
 * Per-exercise progress from the program review, each with the technique the course
 * prescribes for it.
 *
 * The advice sits under the exercise it belongs to rather than in a list of its own:
 * it is the answer to that one lift being stuck, and separating them would make the
 * user match names by hand.
 */
export function ExerciseProgressList({
  exercises,
  techniques,
  skipped,
}: {
  exercises: ExerciseProgress[]
  techniques: ExerciseTechnique[]
  skipped: string[]
}) {
  const sorted = [...exercises].sort((a, b) => ORDER.indexOf(a.status) - ORDER.indexOf(b.status))

  return (
    <div className="space-y-2">
      {sorted.map((exercise) => {
        const status = STATUS[exercise.status]
        const advice = techniques.filter((t) => t.exercise_name === exercise.exercise_name)
        const details = [
          muscleLabel(exercise.muscle_group),
          exercise.best_e1rm ? `e1RM ${formatWeight(exercise.best_e1rm)} кг` : null,
          exercise.change_pct !== null && exercise.change_pct !== undefined
            ? `${exercise.change_pct > 0 ? '+' : ''}${exercise.change_pct}%`
            : null,
          // The count is what separates "answer it inside the exercise" from "change
          // the program", so it is stated rather than left implicit in the badge.
          exercise.stalled_sessions > 1 ? `${exercise.stalled_sessions} сесии на място` : null,
        ]
          .filter(Boolean)
          .join(' · ')

        return (
          <div key={exercise.exercise_name}>
            <ListRow
              title={exercise.exercise_name}
              subtitle={details}
              trailing={<Tag className={status.className}>{status.label}</Tag>}
            />
            {advice.map((technique) => (
              <div
                key={technique.name}
                className="mt-1 rounded-xl border border-ink-700 bg-ink-900 px-4 py-3"
              >
                <p className="label-micro text-volt-400">{technique.title_bg}</p>
                <p className="mt-1.5 text-sm leading-relaxed text-chalk-300">{technique.how_bg}</p>
                <p className="mt-1.5 text-xs text-chalk-500">{technique.source_bg}</p>
              </div>
            ))}
          </div>
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
