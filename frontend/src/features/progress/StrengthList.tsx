import { ListRow } from '../../components/ui'
import { formatWeight } from '../../utils/format'
import { Sparkline } from './Sparkline'
import type { ExerciseStrength } from '../../types/api'

/** Estimated max per exercise and how it moved over the window.
 *
 *  The estimate comes from the backend, computed from the same first-work-set benchmark
 *  the progression engine uses, so this list cannot disagree with the loads prescribed
 *  in the program. */
/** A whole program can carry twenty-odd exercises; the screen is a summary, not a
 *  ledger. The heaviest lifts lead (the backend orders them), and the count is stated
 *  rather than the rest being dropped without a word. */
const VISIBLE = 8

export function StrengthList({ items, weeks }: { items: ExerciseStrength[]; weeks: number }) {
  if (!items.length) {
    return (
      <p className="text-sm leading-relaxed text-chalk-500">
        Още няма достатъчно логнати сесии. Едно упражнение влиза тук след втората
        тренировка, в която е записано.
      </p>
    )
  }

  const shown = items.slice(0, VISIBLE)

  return (
    <div className="space-y-2">
      {shown.map((item) => {
        const gained = item.change_kg > 0
        return (
          <ListRow
            key={item.exercise_name}
            title={item.exercise_name}
            subtitle={
              <>
                1ПМ {formatWeight(item.best_e1rm)} кг ·{' '}
                <span className={gained ? 'font-semibold text-volt-400' : ''}>
                  {gained ? `+${formatWeight(item.change_kg)} кг` : 'без промяна'}
                </span>{' '}
                за {weeks} седмици
              </>
            }
            trailing={<Sparkline points={item.points} />}
          />
        )
      })}
      {items.length > VISIBLE && (
        <p className="pt-1 text-xs text-chalk-500">
          Показани са {VISIBLE} от {items.length} упражнения, подредени по тежест.
        </p>
      )}
    </div>
  )
}
