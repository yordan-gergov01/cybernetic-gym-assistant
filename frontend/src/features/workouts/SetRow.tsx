import { Icon } from '../../components/ui'
import type { SetEntry } from './useWorkoutLogger'

/** One logged set. The tick is a 48px target because it is pressed with sweaty hands,
 *  often without looking, between sets. */
export function SetRow({
  index,
  entry,
  onChange,
}: {
  index: number
  entry: SetEntry
  onChange: (patch: Partial<SetEntry>) => void
}) {
  return (
    <div
      className={`grid grid-cols-[1.75rem_1fr_1fr_1fr_3rem] items-center gap-2 rounded-xl px-1 py-1 transition-colors ${
        entry.done ? 'bg-volt-500/8' : ''
      }`}
    >
      <span className={`text-center text-sm font-bold tabular-nums ${entry.done ? 'text-volt-400' : 'text-chalk-500'}`}>
        {index + 1}
      </span>

      <input
        inputMode="decimal"
        aria-label={`Тегло за серия ${index + 1}`}
        className="input h-11 min-h-0 px-1 text-center font-display text-lg font-semibold tabular-nums"
        placeholder="—"
        value={entry.weight}
        onChange={(e) => onChange({ weight: e.target.value })}
      />
      <input
        inputMode="numeric"
        aria-label={`Повторения за серия ${index + 1}`}
        className="input h-11 min-h-0 px-1 text-center font-display text-lg font-semibold tabular-nums"
        placeholder="—"
        value={entry.reps}
        onChange={(e) => onChange({ reps: e.target.value })}
      />
      <input
        inputMode="numeric"
        aria-label={`RIR за серия ${index + 1}`}
        className="input h-11 min-h-0 px-1 text-center font-display text-lg font-semibold tabular-nums"
        placeholder="—"
        value={entry.rir}
        onChange={(e) => onChange({ rir: e.target.value })}
      />

      <button
        type="button"
        onClick={() => onChange({ done: !entry.done })}
        aria-pressed={entry.done}
        aria-label={entry.done ? `Отмени серия ${index + 1}` : `Завърши серия ${index + 1}`}
        className={`flex h-11 w-12 items-center justify-center rounded-xl border transition-all active:scale-95 ${
          entry.done
            ? 'border-volt-500 bg-volt-500 text-ink-950'
            : 'border-ink-700 bg-ink-900 text-ink-600'
        }`}
      >
        <Icon name="check" size={20} />
      </button>
    </div>
  )
}
