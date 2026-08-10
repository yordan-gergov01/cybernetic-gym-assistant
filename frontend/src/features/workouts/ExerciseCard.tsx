import type { ProgramExercise } from '../../types/api'
import { SetRow } from './SetRow'
import type { SetEntry } from './useWorkoutLogger'

export function ExerciseCard({
  exercise,
  rows,
  onChangeRow,
}: {
  exercise: ProgramExercise
  rows: SetEntry[]
  onChangeRow: (index: number, patch: Partial<SetEntry>) => void
}) {
  const doneCount = rows.filter((r) => r.done).length
  const allDone = doneCount === rows.length

  return (
    <section
      className={`card transition-colors ${allDone ? 'border-volt-500/40' : ''}`}
      aria-label={exercise.exercise_name}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="font-display text-lg leading-tight font-semibold tracking-wide">
            {exercise.exercise_name}
          </h2>
          <p className="mt-1 text-xs text-chalk-500">
            {exercise.reps_min}–{exercise.reps_max} повт. · RIR {exercise.rir_target ?? 2}
            {exercise.rest_seconds ? ` · ${Math.round(exercise.rest_seconds / 60)} мин почивка` : ''}
          </p>
        </div>
        <span
          className={`shrink-0 rounded-full px-2.5 py-1 text-[11px] font-bold tabular-nums ${
            allDone ? 'bg-volt-500 text-ink-950' : 'bg-ink-700 text-chalk-300'
          }`}
        >
          {doneCount}/{rows.length}
        </span>
      </div>

      {exercise.target_note && (
        <p className="mb-3 rounded-lg border border-volt-500/25 bg-volt-500/8 px-3 py-2 text-xs leading-relaxed text-volt-400">
          {exercise.target_note}
        </p>
      )}

      <div className="mb-1.5 grid grid-cols-[1.75rem_1fr_1fr_1fr_3rem] gap-2 px-1 text-[10px] font-semibold tracking-[0.1em] text-chalk-500 uppercase">
        <span className="text-center">сет</span>
        <span className="text-center">кг</span>
        <span className="text-center">повт.</span>
        <span className="text-center">RIR</span>
        <span />
      </div>

      <div className="space-y-1.5">
        {rows.map((row, index) => (
          <SetRow key={index} index={index} entry={row} onChange={(patch) => onChangeRow(index, patch)} />
        ))}
      </div>
    </section>
  )
}
