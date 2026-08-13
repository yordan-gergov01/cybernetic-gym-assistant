import { Icon } from '../../components/ui'
import { muscleLabel } from '../../constants/muscles'
import type { ProgramDay, ProgramWeek } from '../../types/api'

export type DayStatus = 'done' | 'today' | 'upcoming'

/** What the day trains, from the exercises themselves - the plan has no "focus" field
 *  and inventing one in the client would let it disagree with the exercises below it. */
function dayFocus(day: ProgramDay): string {
  const muscles: string[] = []
  for (const exercise of day.exercises) {
    const label = muscleLabel(exercise.muscle_group)
    if (label && !muscles.includes(label)) muscles.push(label)
  }
  return [muscles.slice(0, 2).join(', '), `${day.exercises.length} упражнения`]
    .filter(Boolean)
    .join(' · ')
}

function StatusTag({ status }: { status: DayStatus }) {
  if (status === 'done') {
    return (
      <span className="flex shrink-0 items-center gap-1 text-xs text-volt-500">
        <Icon name="check" size={14} /> Завършена
      </span>
    )
  }
  if (status === 'today') {
    return (
      <span className="shrink-0 rounded-lg border border-volt-500 px-2 py-0.5 text-[11px] font-semibold text-volt-400">
        Днес
      </span>
    )
  }
  return <span className="shrink-0 text-xs text-chalk-500">Предстои</span>
}

/**
 * The whole plan, one collapsed card per week.
 *
 * Only one week is open at a time: twenty weeks of days expanded at once is a wall of
 * text on a phone, and the week the user came for is almost always the current one.
 */
export function WeekAccordion({
  weeks,
  openWeek,
  onToggleWeek,
  dayStatus,
  onOpenDay,
}: {
  weeks: ProgramWeek[]
  openWeek: number | null
  onToggleWeek: (weekNumber: number) => void
  /** Asked per training day, by week and by its slot in that week's rotation - rest
   *  days do not take a slot, because the backend's rotation skips them. */
  dayStatus: (weekNumber: number, slot: number) => DayStatus
  onOpenDay: (day: ProgramDay) => void
}) {
  return (
    <div className="space-y-2">
      {[...weeks]
        .sort((a, b) => a.week_number - b.week_number)
        .map((week: ProgramWeek) => {
          const isOpen = openWeek === week.week_number
          const days = [...week.days].sort((a, b) => a.day_number - b.day_number)
          let slot = -1

          return (
            <div key={week.id} className="card-surface overflow-hidden">
              <button
                type="button"
                onClick={() => onToggleWeek(week.week_number)}
                aria-expanded={isOpen}
                className="tap flex w-full items-center gap-3 p-4 text-left"
              >
                <span className="num text-lg font-semibold text-chalk-50">
                  Седмица {week.week_number}
                </span>
                <span
                  className={`rounded-lg border px-2 py-0.5 text-[11px] font-semibold tracking-wider uppercase ${
                    week.week_type === 'deload'
                      ? 'border-danger-400/40 bg-danger-400/10 text-danger-400'
                      : 'border-ink-700 bg-ink-900 text-chalk-500'
                  }`}
                >
                  {week.week_type === 'deload' ? 'Deload' : 'Натоварване'}
                </span>
                <Icon
                  name="chevronDown"
                  size={18}
                  className={`ml-auto shrink-0 text-chalk-500 transition-transform ${
                    isOpen ? 'rotate-180' : ''
                  }`}
                />
              </button>

              {isOpen && (
                <div className="anim-in divide-y divide-ink-700 border-t border-ink-700">
                  {days.map((day) => {
                    if (!day.is_rest_day) slot += 1
                    const daySlot = slot
                    return day.is_rest_day ? (
                      <div key={day.id} className="flex items-center gap-3 p-4">
                        <p className="min-w-0 flex-1 truncate text-[15px] text-chalk-500">
                          {day.day_name || `Ден ${day.day_number}`}
                        </p>
                        <span className="shrink-0 text-xs text-chalk-500">Почивка</span>
                      </div>
                    ) : (
                      <button
                        key={day.id}
                        type="button"
                        onClick={() => onOpenDay(day)}
                        className="tap flex w-full items-center gap-3 p-4 text-left"
                      >
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-[15px] font-medium text-chalk-50">
                            {day.day_name || `Ден ${day.day_number}`}
                          </p>
                          <p className="num text-xs text-chalk-500">{dayFocus(day)}</p>
                        </div>
                        <StatusTag status={dayStatus(week.week_number, daySlot)} />
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
    </div>
  )
}
