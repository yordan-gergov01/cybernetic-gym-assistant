import { Icon } from '../../components/ui'
import { MEAL_LABELS, MEAL_ORDER } from '../../constants/nutrition'
import { formatGrams, formatKcal } from '../../utils/format'
import type { FoodEntry } from '../../types/api'

const UNGROUPED = 'other'

/** Entries grouped by meal, in the order of a day.
 *
 *  Anything logged before meals were recorded has no meal on it; those go in their own
 *  group at the end rather than being folded into breakfast. */
export function FoodEntryList({
  entries,
  onDelete,
  deletingId,
}: {
  entries: FoodEntry[]
  onDelete: (id: string) => void
  deletingId?: string
}) {
  const groups = [...MEAL_ORDER, UNGROUPED]
    .map((meal) => ({
      meal,
      rows: entries.filter((e) => (e.meal_type || UNGROUPED) === meal),
    }))
    .filter((group) => group.rows.length > 0)

  return (
    <div className="space-y-4">
      {groups.map(({ meal, rows }) => (
        <div key={meal}>
          <p className="label-micro mb-2">{MEAL_LABELS[meal] ?? 'Друго'}</p>
          <div className="space-y-2">
            {rows.map((entry) => (
              <div key={entry.id} className="card-surface flex items-center gap-3 p-3.5">
                <div className="min-w-0 flex-1">
                  <p className="flex items-center gap-2 truncate text-[15px] font-medium text-chalk-50">
                    <span className="truncate">{entry.food_name}</span>
                    {/* Numbers the model estimated are marked, so they are not read as
                        measured values from the food database. */}
                    {entry.source !== 'USDA' && (
                      <span className="shrink-0 rounded-md border border-warn-400/40 bg-warn-400/10 px-1.5 py-0.5 text-[10px] font-semibold tracking-wider text-warn-400 uppercase">
                        оценка
                      </span>
                    )}
                  </p>
                  <p className="num mt-0.5 text-[13px] text-chalk-500">
                    {entry.quantity_g ? `${formatGrams(entry.quantity_g)} г · ` : ''}
                    {formatKcal(entry.calories)} ккал · {formatGrams(entry.protein_g)} г протеин
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => onDelete(entry.id)}
                  disabled={deletingId === entry.id}
                  aria-label={`Изтрий ${entry.food_name}`}
                  className="tap grid h-11 w-11 shrink-0 place-items-center rounded-xl text-chalk-500 active:bg-danger-400/10 active:text-danger-400 disabled:opacity-40"
                >
                  <Icon name="trash" size={18} />
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
