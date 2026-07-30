import { Stat } from '../../components/ui'
import { formatDelta } from '../../utils/format'
import type { WeightCoaching } from '../../types/api'

/** The calorie recommendation is computed deterministically on the backend; this only
 *  presents it, including the "you're on track" case. */
export function CoachingCard({ coaching }: { coaching: WeightCoaching }) {
  if (coaching.status !== 'ok') return null
  const onTrack = coaching.on_track

  return (
    <section
      className={`card ${onTrack ? 'border-ok-400/35 bg-ok-400/[0.06]' : 'border-warn-400/35 bg-warn-400/[0.06]'}`}
    >
      <div className="mb-2 flex items-center gap-2">
        <span
          className={`h-2 w-2 rounded-full ${onTrack ? 'bg-ok-400' : 'bg-warn-400'}`}
          aria-hidden="true"
        />
        <h2 className="font-display text-base font-semibold tracking-[0.08em] uppercase">
          {onTrack ? 'В графика' : 'Нужна е корекция'}
        </h2>
      </div>

      <p className="text-sm leading-relaxed text-chalk-300">{coaching.recommendation}</p>

      {!onTrack && coaching.new_calorie_target && (
        <div className="mt-4 flex items-end gap-8 border-t border-ink-700 pt-4">
          <Stat value={coaching.new_calorie_target} unit="ккал" label="нова дневна цел" tone="warn" size="sm" />
          <Stat value={formatDelta(coaching.calorie_delta)} label="промяна" size="sm" />
        </div>
      )}
    </section>
  )
}
