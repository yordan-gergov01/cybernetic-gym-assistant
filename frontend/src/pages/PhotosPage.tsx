import { useQuery } from '@tanstack/react-query'
import { SubPageHeader } from '../components/layout/SubPageHeader'
import { EmptyState, ErrorNote, Icon, Loading } from '../components/ui'
import { queryKeys } from '../constants/query-keys'
import { photosApi } from '../features/photos/api'
import { formatShortDate } from '../utils/date'

/** Assessment history: every set of photos with the percentage it produced.
 *
 *  A new assessment is not started here - it is the same flow the setup uses, so it
 *  lives with the body-fat step and this screen links into it rather than keeping a
 *  second copy of the upload and confidence handling. */
export function PhotosPage() {
  const photos = useQuery({ queryKey: queryKeys.photos, queryFn: photosApi.list })
  const items = photos.data ?? []

  return (
    <div className="min-h-dvh bg-ink-950">
      <SubPageHeader title="Снимки" />

      <main className="mx-auto max-w-lg px-4 pt-4 pb-12">
        {photos.isLoading ? (
          <Loading />
        ) : photos.error ? (
          <ErrorNote error={photos.error} onRetry={() => photos.refetch()} />
        ) : (
          <>
            {!items.length ? (
              <EmptyState
                title="Още няма снимки"
                hint="Снимки отпред, отстрани и отзад дават оценка на телесните мазнини по визуалния справочник на курса."
              />
            ) : (
              <div className="grid grid-cols-3 gap-2">
                {items.map((photo) => (
                  <figure
                    key={photo.id}
                    className="relative aspect-3/4 overflow-hidden rounded-xl border border-ink-700 bg-ink-900"
                  >
                    {photo.url ? (
                      <img src={photo.url} alt="" className="h-full w-full object-cover" />
                    ) : (
                      <span className="grid h-full place-items-center text-chalk-500">
                        <Icon name="camera" size={20} />
                      </span>
                    )}
                    <figcaption className="absolute inset-x-0 bottom-0 bg-ink-950/85 px-2 py-1.5">
                      {photo.bf_pct_assessed !== null && photo.bf_pct_assessed !== undefined && (
                        <span className="block text-xs font-bold tabular-nums">
                          {photo.bf_pct_assessed}%
                        </span>
                      )}
                      <span className="block text-[11px] text-chalk-500">
                        {formatShortDate(photo.taken_at)}
                      </span>
                    </figcaption>
                  </figure>
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
