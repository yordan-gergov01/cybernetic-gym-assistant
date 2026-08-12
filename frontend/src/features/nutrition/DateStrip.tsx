import { formatDayChip } from '../../utils/date'

/** The last few days, so yesterday's log is one tap away.
 *
 *  It only goes backwards: there is nothing to log for a day that has not happened. */
export function DateStrip({
  dates,
  selected,
  onSelect,
}: {
  dates: string[]
  selected: string
  onSelect: (date: string) => void
}) {
  return (
    <div className="no-scrollbar flex gap-2 overflow-x-auto">
      {dates.map((date) => {
        const active = date === selected
        return (
          <button
            key={date}
            type="button"
            onClick={() => onSelect(date)}
            aria-pressed={active}
            className={`tap min-h-11 shrink-0 rounded-xl border px-4 text-sm font-medium ${
              active
                ? 'border-volt-500 bg-volt-500/8 text-volt-400'
                : 'border-ink-700 bg-ink-800 text-chalk-500'
            }`}
          >
            {formatDayChip(date)}
          </button>
        )
      })}
    </div>
  )
}
