import { Link } from 'react-router-dom'
import { Icon, type IconName } from '../ui'

type HeaderAction = { to: string; icon: IconName; label: string; badge?: boolean }

/**
 * Sticky screen header. Owns the notch inset itself (rather than the body) so
 * full-bleed screens can still reach the top edge. Action targets are 48px - the
 * minimum that stays hittable one-handed.
 */
export function AppHeader({
  title,
  subtitle,
  actions = [],
}: {
  title: string
  subtitle?: string
  actions?: HeaderAction[]
}) {
  return (
    <header className="sticky top-0 z-30 border-b border-ink-700 bg-ink-950/90 backdrop-blur">
      <div
        className="mx-auto grid max-w-lg grid-cols-[minmax(0,1fr)_auto] items-center gap-3 px-4 pb-3"
        style={{ paddingTop: 'calc(env(safe-area-inset-top) + 14px)' }}
      >
        <div className="min-w-0">
          <h1 className="section-title truncate text-chalk-50">{title}</h1>
          {subtitle && <p className="truncate text-xs text-chalk-500">{subtitle}</p>}
        </div>

        {actions.length > 0 && (
          <div className="flex shrink-0 items-center gap-1">
            {actions.map((action) => (
              <Link
                key={action.to}
                to={action.to}
                aria-label={action.label}
                className="tap relative grid h-12 w-12 place-items-center rounded-xl text-chalk-300 active:bg-ink-800"
              >
                <Icon name={action.icon} />
                {action.badge && (
                  <span className="absolute top-2.5 right-2.5 h-2 w-2 rounded-full bg-volt-500 ring-2 ring-ink-950" />
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
    </header>
  )
}
