const DAY_LABELS = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'НД']

export type DayStatus = 'done' | 'today' | 'rest' | 'upcoming'

/** Week at a glance. Gives the "where am I in the plan" context that a single day
 *  screen cannot, without leaving the tab. */
export function WeekStrip({
  statuses,
  onSelect,
}: {
  statuses: DayStatus[]
  onSelect?: (index: number) => void
}) {
  return (
    <div className="mb-4 flex gap-1.5">
      {DAY_LABELS.map((label, index) => {
        const status = statuses[index] ?? 'upcoming'
        const isToday = status === 'today'
        return (
          <button
            key={label}
            type="button"
            onClick={() => onSelect?.(index)}
            aria-label={`${label}${isToday ? ' — днес' : ''}`}
            aria-current={isToday ? 'date' : undefined}
            className={`tap flex flex-1 flex-col items-center gap-1.5 rounded-xl border py-2 ${
              isToday
                ? 'border-volt-500 bg-volt-500/10'
                : status === 'done'
                  ? 'border-ink-700 bg-ink-800'
                  : 'border-ink-700/60 bg-transparent'
            }`}
          >
            <span
              className={`text-[10px] font-semibold tracking-wider ${
                isToday ? 'text-volt-400' : 'text-chalk-500'
              }`}
            >
              {label}
            </span>
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                status === 'done'
                  ? 'bg-volt-500'
                  : isToday
                    ? 'bg-volt-400'
                    : status === 'rest'
                      ? 'bg-transparent ring-1 ring-ink-600'
                      : 'bg-ink-600'
              }`}
            />
          </button>
        )
      })}
    </div>
  )
}
