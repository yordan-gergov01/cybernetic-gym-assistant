import { MACROS } from '../../constants/nutrition'
import { Meter } from '../../components/ui'
import { formatGrams, formatKcal } from '../../utils/format'
import type { DailyNutrition } from '../../types/api'

/** Calories first and largest, then the macros under it.
 *
 *  Protein is drawn heavier than the other two: it is the one a lifter has to hit, and
 *  the others follow from the calorie budget. */
export function MacroSummary({ daily }: { daily: DailyNutrition }) {
  const kcal = daily.totals.calories ?? 0
  const target = daily.targets.calories ?? 0
  const remaining = Math.round(target - kcal)
  const over = remaining < 0

  return (
    <section className="card">
      <p className="label-micro">Калории</p>
      <p className="num mt-1 text-5xl font-semibold text-chalk-50">
        {formatKcal(kcal)}
        {target > 0 && <span className="ml-2 text-xl text-chalk-500">/ {formatKcal(target)} ккал</span>}
      </p>
      {target > 0 && (
        <p className={`num mt-1 text-sm ${over ? 'text-warn-400' : 'text-chalk-300'}`}>
          {over ? `+${Math.abs(remaining)} над целта` : `Остават ${remaining}`}
        </p>
      )}

      <div className="mt-3">
        <Meter value={kcal} max={target || 1} tone={over ? 'warn' : 'accent'} size="lg" />
      </div>

      <div className="mt-5 space-y-3">
        {MACROS.map((macro) => {
          const value = daily.totals[macro.key] ?? 0
          const macroTarget = daily.targets[macro.key] ?? 0
          const priority = macro.key === 'protein_g'
          return (
            <div key={macro.key}>
              <div className="mb-1.5 flex items-end justify-between">
                <span
                  className={`text-sm ${priority ? 'font-semibold text-chalk-50' : 'text-chalk-300'}`}
                >
                  {macro.label}
                </span>
                <span className="num text-sm text-chalk-300">
                  {formatGrams(value)} / {macroTarget ? formatGrams(macroTarget) : '—'} {macro.unit}
                </span>
              </div>
              <Meter
                value={value}
                max={macroTarget || 1}
                tone={macro.tone}
                size={priority ? 'md' : 'sm'}
              />
            </div>
          )
        })}
      </div>
    </section>
  )
}
