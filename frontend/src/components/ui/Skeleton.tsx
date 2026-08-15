/** A placeholder in the shape of the thing that is loading.
 *
 *  Used instead of a spinner where the layout is known in advance: the screen keeps its
 *  proportions while the data arrives, so nothing jumps under the thumb once it does. */
export function Skeleton({ className = '' }: { className?: string }) {
  return <div aria-hidden className={`anim-soft rounded-xl bg-ink-800 ${className}`} />
}

/** The standard loading body: a headline block over a few rows.
 *
 *  `role="status"` with a label, because the blocks themselves say nothing to a screen
 *  reader - without it a blind user gets silence while the screen is busy. */
export function SkeletonList({ rows = 4, lead = true }: { rows?: number; lead?: boolean }) {
  return (
    <div role="status" aria-label="Зареждане" className="space-y-2">
      {lead && <Skeleton className="mb-4 h-28 w-full rounded-2xl" />}
      {Array.from({ length: rows }, (_, index) => (
        <Skeleton key={index} className="h-16 w-full rounded-2xl" />
      ))}
    </div>
  )
}
