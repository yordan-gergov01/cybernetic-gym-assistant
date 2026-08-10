import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { Icon } from '../ui'

/** Header for a screen opened from another one — photos, notifications, the check-in.
 *
 *  It carries its own back control because the app runs installed, where there is no
 *  browser chrome to go back with. */
export function SubPageHeader({
  title,
  action,
  onBack,
}: {
  title: string
  action?: ReactNode
  onBack?: () => void
}) {
  const navigate = useNavigate()

  return (
    <header className="sticky top-0 z-30 border-b border-ink-700 bg-ink-950/95 backdrop-blur">
      <div
        className="mx-auto flex max-w-lg items-center gap-2 px-4 pb-3"
        style={{ paddingTop: 'calc(env(safe-area-inset-top) + 12px)' }}
      >
        <button
          type="button"
          onClick={onBack ?? (() => navigate(-1))}
          aria-label="Назад"
          className="tap -ml-2 grid h-11 w-11 shrink-0 place-items-center rounded-xl text-chalk-300 active:bg-ink-800"
        >
          <Icon name="chevronLeft" size={22} />
        </button>
        <h1 className="section-title min-w-0 flex-1 truncate">{title}</h1>
        {action}
      </div>
    </header>
  )
}
