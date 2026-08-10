import { Tag } from '../../components/ui'
import type { SessionEstimate } from '../../types/api'

/** The "what am I in for" card, read before the first set.
 *
 *  Session length is prefixed with a tilde on purpose: it is an estimate built from the
 *  prescribed rest intervals, and presenting it as exact would be a small lie the user
 *  discovers on their first session. */
export function SessionCard({
  title,
  estimate,
  onStart,
  starting = false,
}: {
  title: string
  estimate?: SessionEstimate | null
  onStart: () => void
  starting?: boolean
}) {
  return (
    <section className="card">
      <p className="label-micro">Днешната сесия</p>
      <h2 className="mt-2 font-display text-3xl leading-none font-bold">{title}</h2>

      {estimate && (
        <div className="mt-3 flex flex-wrap gap-2">
          <Tag pill>{estimate.exercise_count} упражнения</Tag>
          <Tag pill>~{estimate.total_sets} серии</Tag>
          <Tag pill>~{estimate.minutes} мин</Tag>
        </div>
      )}

      <button type="button" onClick={onStart} disabled={starting} className="btn-primary w-full mt-5">
        {starting ? 'Момент…' : 'Започни тренировката'}
      </button>
    </section>
  )
}
