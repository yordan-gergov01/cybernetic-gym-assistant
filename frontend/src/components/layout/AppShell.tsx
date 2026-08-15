import { Outlet } from 'react-router-dom'
import { BottomNav } from './BottomNav'
import { OfflineBanner } from './OfflineBanner'

/** Screens render their own AppHeader so each can set its own title, subtitle and
 *  actions; the shell only owns the scroll container and what is pinned to the bottom.
 *
 *  The offline strip sits in the same fixed stack as the nav rather than at the top of
 *  the page: every screen has its own sticky header up there, and a banner over it would
 *  cover the title of whatever the user is looking at. */
export function AppShell() {
  return (
    <div className="flex min-h-dvh flex-col bg-ink-950">
      <div className="flex-1 pb-24">
        <Outlet />
      </div>
      <div className="fixed inset-x-0 bottom-0 z-40">
        <OfflineBanner />
        <BottomNav />
      </div>
    </div>
  )
}
