import { Link } from 'react-router-dom'
import { Icon } from '../../components/ui'
import { formatShortDate } from '../../utils/date'
import type { UserPhoto } from '../../types/api'

/** Current body fat plus the assessment history as thumbnails. */
export function BodyCompositionCard({
  bodyFatPct,
  photos,
}: {
  bodyFatPct?: number | null
  photos: UserPhoto[]
}) {
  const assessed = photos.filter((p) => p.bf_pct_assessed !== null && p.bf_pct_assessed !== undefined)

  return (
    <section className="card">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="label-micro">Текущи мазнини</p>
          <p className="stat mt-2">{bodyFatPct !== null && bodyFatPct !== undefined ? `${bodyFatPct}%` : '—'}</p>
        </div>
        <Link
          to="/photos"
          aria-label="Нова оценка по снимки"
          className="tap grid h-12 w-12 shrink-0 place-items-center rounded-full bg-volt-500 text-ink-950"
        >
          <Icon name="camera" size={20} />
        </Link>
      </div>

      {assessed.length > 0 && (
        <div className="mt-4 grid grid-cols-4 gap-2">
          {assessed.slice(0, 4).map((photo) => (
            <div
              key={photo.id}
              className="relative aspect-3/4 overflow-hidden rounded-xl border border-ink-700 bg-ink-900"
            >
              {photo.url && <img src={photo.url} alt="" className="h-full w-full object-cover" />}
              <span className="absolute inset-x-0 bottom-0 bg-ink-950/80 px-1.5 py-1 text-center text-[11px] font-bold tabular-nums">
                {photo.bf_pct_assessed}%
              </span>
              <span className="sr-only">{formatShortDate(photo.taken_at)}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
