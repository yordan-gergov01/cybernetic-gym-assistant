import { Outlet } from 'react-router-dom'
import { BottomNav } from './BottomNav'

/** Screens render their own AppHeader so each can set its own title, subtitle and
 *  actions; the shell only owns the scroll container and the bottom nav. */
export function AppShell() {
  return (
    <div className="flex min-h-dvh flex-col bg-ink-950">
      <div className="flex-1 pb-24">
        <Outlet />
      </div>
      <BottomNav />
    </div>
  )
}
