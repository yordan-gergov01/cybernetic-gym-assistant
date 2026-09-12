import { Icon, Meter } from '../../components/ui'
import { formatClock } from '../../utils/format'
import { REST_EXTENSION_SECONDS } from './useRestTimer'

/** The rest countdown, pinned above the finish button.
 *
 *  It sits at the bottom because that is where a thumb already is between sets, and it
 *  keeps its own row so the set the user just ticked stays visible above it. */
export function RestTimerBar({
  remaining,
  total,
  onExtend,
  onSkip,
}: {
  remaining: number
  total: number
  onExtend: () => void
  onSkip: () => void
}) {
  const over = remaining === 0

  return (
    <div
      role="timer"
      aria-live="off"
      aria-label={over ? 'Почивката свърши' : `Почивка: остават ${remaining} секунди`}
      // Opaque, not a tint: it floats over the next exercise card, and a translucent
      // bar lets that card's text show through the countdown.
      className={`flex items-center gap-3 rounded-xl border bg-ink-900 px-3 py-2 shadow-lg shadow-ink-950/80 transition-colors ${
        over ? 'border-ok-400/60' : 'border-volt-500/50'
      }`}
    >
      <Icon name="timer" size={18} className={over ? 'shrink-0 text-ok-400' : 'shrink-0 text-volt-500'} />
      <span
        className={`shrink-0 font-display text-lg font-semibold tabular-nums ${
          over ? 'text-ok-400' : 'text-volt-400'
        }`}
      >
        {over ? 'Давай' : formatClock(remaining)}
      </span>

      <div className="min-w-0 flex-1">
        <Meter value={total - remaining} max={total} tone={over ? 'ok' : 'accent'} />
      </div>

      <button
        type="button"
        onClick={onExtend}
        className="shrink-0 rounded-lg px-2 py-1 text-xs font-semibold text-chalk-300 active:scale-95"
      >
        +{REST_EXTENSION_SECONDS}с
      </button>
      <button
        type="button"
        onClick={onSkip}
        className="shrink-0 rounded-lg px-2 py-1 text-xs font-semibold text-chalk-500 active:scale-95"
      >
        {over ? 'Скрий' : 'Пропусни'}
      </button>
    </div>
  )
}
