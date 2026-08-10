import type { ReactNode } from 'react'

/** Metadata capsule: set counts, session length, the muscle an exercise trains.
 *
 *  Deliberately quiet. It annotates something else on the row and must never read as
 *  the thing itself. */
export function Tag({
  children,
  pill = false,
  className = '',
}: {
  children: ReactNode
  pill?: boolean
  className?: string
}) {
  return <span className={`${pill ? 'tag-pill' : 'tag'} ${className}`}>{children}</span>
}
