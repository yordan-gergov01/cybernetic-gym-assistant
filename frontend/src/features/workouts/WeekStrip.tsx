import { Icon } from '../../components/ui'
import { WEEK_STRIP_LABELS } from '../../constants/calendar'
import type { CalendarDay } from '../../types/api'

/** The current week at a glance: which days were trained, and which one is today.
 *
 *  It reports what was logged rather than what was planned, because the program stores
 *  a rotation of days, not a weekday timetable - claiming "legs on Friday" would be an
 *  invention. Trained days carry a tick as well as the accent colour, so the state does
 *  not depend on telling two greens apart. */
export function WeekStrip({ days }: { days: CalendarDay[] }) {
  return (
    <div className="grid grid-cols-7 gap-1.5">
      {days.map((day, index) => (
        <div
          key={day.date}
          className={`rounded-2xl border py-2.5 text-center ${
            day.is_today ? 'border-volt-500 bg-volt-500/5' : 'border-ink-700 bg-ink-800'
          }`}
        >
          <div className={`text-[10px] font-bold tracking-wider ${day.is_today ? 'text-volt-400' : 'text-chalk-500'}`}>
            {WEEK_STRIP_LABELS[index]}
          </div>
          <div className="mt-2 grid place-items-center">
            {day.trained ? (
              <span className="grid h-5 w-5 place-items-center rounded-full bg-volt-500/20 text-volt-400">
                <Icon name="check" size={12} />
              </span>
            ) : day.is_today ? (
              <span className="h-5 w-5 rounded-full bg-volt-500" />
            ) : (
              <span className="h-5 w-5 rounded-full border border-ink-600" />
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
