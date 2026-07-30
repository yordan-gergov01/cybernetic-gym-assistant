import type { ReactNode } from 'react'
import { AppHeader } from './AppHeader'
import type { IconName } from '../ui'

type Action = { to: string; icon: IconName; label: string; badge?: boolean }

/** Standard screen frame: sticky header + a max-width, padded content column.
 *  Every tab screen uses this so headers and gutters stay identical. */
export function Screen({
  title,
  subtitle,
  actions,
  children,
}: {
  title: string
  subtitle?: string
  actions?: Action[]
  children: ReactNode
}) {
  return (
    <>
      <AppHeader title={title} subtitle={subtitle} actions={actions} />
      <div className="mx-auto w-full max-w-lg px-4 pt-4">{children}</div>
    </>
  )
}
