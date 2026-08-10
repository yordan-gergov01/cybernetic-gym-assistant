import { muscleLabel } from '../../constants/muscles'
import type { MuscleVolume } from '../../types/api'

/** Sets done this week against the planned volume, per muscle.
 *
 *  Both numbers come from the backend - the target from the volume calculator, the count
 *  from the log - so the bar can never disagree with the plan it is drawn against.
 *  A muscle trained without a target is shown too, with its count and no bar: work
 *  happening outside the plan is exactly what needs to be visible. */
export function WeeklyVolume({ volume }: { volume: MuscleVolume[] }) {
  if (!volume.length) {
    return <p className="text-sm text-chalk-500">Още няма логнати серии тази седмица.</p>
  }

  return (
    <div className="space-y-3">
      {volume.map((muscle) => {
        const target = muscle.sets_target
        const pct = target && target > 0 ? Math.min(100, (muscle.sets_done / target) * 100) : null
        return (
          <div key={muscle.muscle_group}>
            <div className="flex items-baseline justify-between gap-3">
              <span className="text-sm font-medium text-chalk-50">
                {muscleLabel(muscle.muscle_group)}
              </span>
              <span className="num text-xs text-chalk-500">
                {target ? `${muscle.sets_done} / ${target} серии` : `${muscle.sets_done} серии · без цел`}
              </span>
            </div>
            <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-ink-700">
              {pct !== null && (
                <div
                  className="h-full rounded-full bg-volt-500 transition-[width]"
                  style={{ width: `${pct}%` }}
                />
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
