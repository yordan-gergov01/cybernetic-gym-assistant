import { Icon } from '../../components/ui'
import { formatGrams, formatKcal } from '../../utils/format'
import type { DailyNutrition } from '../../types/api'

export function FoodEntryList({
  entries,
  onDelete,
}: {
  entries: DailyNutrition['entries']
  onDelete: (id: string) => void
}) {
  if (!entries.length) {
    return <p className="py-10 text-center text-sm text-chalk-500">Още нищо за днес.</p>
  }

  return (
    <ul className="space-y-2">
      {entries.map((entry) => (
        <li key={entry.id} className="card flex items-center justify-between gap-3 py-3">
          <div className="min-w-0">
            <p className="truncate font-medium">{entry.food_name}</p>
            <p className="mt-0.5 text-xs text-chalk-500 tabular-nums">
              {entry.quantity_g ? `${formatGrams(entry.quantity_g)} г · ` : ''}
              {formatKcal(entry.calories)} ккал · {formatGrams(entry.protein_g)} г протеин
            </p>
          </div>
          <button
            onClick={() => onDelete(entry.id)}
            aria-label={`Изтрий ${entry.food_name}`}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-chalk-500 active:bg-ink-700"
          >
            <Icon name="close" size={16} />
          </button>
        </li>
      ))}
    </ul>
  )
}
