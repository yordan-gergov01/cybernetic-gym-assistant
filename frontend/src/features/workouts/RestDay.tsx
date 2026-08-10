import { Icon, ListRow, Ring, SectionHeader, StatBox } from '../../components/ui'
import { formatShortDate } from '../../utils/date'
import { WeeklyVolume } from './WeeklyVolume'
import type { TodayView } from '../../types/api'

/** The rest-day face of the Today screen.
 *
 *  A rest day is not an empty screen: it is when the weekly picture and the two things
 *  that keep the plan honest - the weigh-in and the recovery check-in - are worth
 *  surfacing, because there is nothing else competing for attention. */
export function RestDay({ today, needsWeighIn }: { today: TodayView; needsWeighIn: boolean }) {
  const last = today.last_session

  return (
    <>
      <section className="card flex flex-col items-center gap-2 py-10 text-center">
        <span className="grid h-14 w-14 place-items-center rounded-2xl bg-ink-900 text-chalk-300">
          <Icon name="moon" size={26} />
        </span>
        <h2 className="mt-2 font-display text-xl font-bold tracking-[0.1em] uppercase">
          Почивен ден
        </h2>
        <p className="text-sm text-chalk-500">Възстановяването е част от програмата.</p>
      </section>

      <div className="mt-3 grid grid-cols-2 gap-3">
        <div className="grid place-items-center rounded-2xl border border-ink-700 bg-ink-900 p-4">
          <Ring
            value={today.sessions_this_week}
            max={today.sessions_planned || today.sessions_this_week}
            label="тренировки"
          />
        </div>

        {last ? (
          <StatBox
            label={`Последна · ${formatShortDate(last.date)}`}
            value={Math.round(last.tonnage_kg).toLocaleString('bg-BG')}
            unit="кг"
            footer={`${last.working_sets} серии`}
          />
        ) : (
          <StatBox label="Последна тренировка" value="—" footer="Още няма логнати серии" />
        )}
      </div>

      <div className="mt-3 space-y-2">
        {needsWeighIn && (
          <ListRow
            to="/progress"
            accent
            leading={<Icon name="scale" size={18} />}
            title="Липсва измерване днес"
            subtitle="Дневното тегло захранва тренда."
            chevron
          />
        )}
        <ListRow
          to="/check-in"
          leading={<Icon name="target" size={18} />}
          title="Седмичен чек-ин"
          subtitle="6 въпроса · решава дали ти трябва deload."
          chevron
        />
      </div>

      <SectionHeader title="Седмичен обем" />
      <WeeklyVolume volume={today.weekly_volume} />
    </>
  )
}
