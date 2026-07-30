import { MACROS } from '../../constants/nutrition'
import { Meter, Stat } from '../../components/ui'
import { formatGrams, formatKcal } from '../../utils/format'
import type { DailyNutrition } from '../../types/api'

export function MacroSummary({ daily }: { daily: DailyNutrition }) {
  const kcal = daily.totals.calories ?? 0
  const kcalTarget = daily.targets.calories ?? 0
  const remaining = Math.round(kcalTarget - kcal)
  const over = remaining < 0

  return (
    <section className="card mb-4">
      <div className="mb-4 flex items-end justify-between gap-4">
        <Stat
          value={formatKcal(kcal)}
          unit={kcalTarget ? `/ ${formatKcal(kcalTarget)}` : undefined}
          label="ккал днес"
          tone="accent"
        />
        <Stat
          value={over ? `+${Math.abs(remaining)}` : remaining}
          label={over ? 'над целта' : 'остават'}
          tone={over ? 'danger' : 'default'}
          size="sm"
        />
      </div>

      <Meter value={kcal} max={kcalTarget || 1} tone={over ? 'danger' : 'accent'} />

      <div className="mt-5 space-y-3.5">
        {MACROS.map((macro) => {
          const value = daily.totals[macro.key] ?? 0
          const target = daily.targets[macro.key] ?? 0
          return (
            <div key={macro.key}>
              <div className="mb-1.5 flex items-baseline justify-between text-xs">
                <span className="font-semibold tracking-[0.08em] text-chalk-300 uppercase">{macro.label}</span>
                <span className="tabular-nums text-chalk-500">
                  <span className="font-semibold text-chalk-50">{formatGrams(value)}</span>
                  {' / '}
                  {target ? formatGrams(target) : '—'} {macro.unit}
                </span>
              </div>
              <Meter value={value} max={target || 1} tone={macro.tone} />
            </div>
          )
        })}
      </div>
    </section>
  )
}
