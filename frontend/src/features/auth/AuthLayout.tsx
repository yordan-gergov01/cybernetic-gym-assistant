import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Icon } from '../../components/ui'

/** Shared frame for the login and register screens.
 *
 *  Both are reached from the landing page, so both need a way back that is not the
 *  browser's - a PWA in standalone mode has no back button of its own. */
export function AuthLayout({
  eyebrow,
  title,
  intro,
  children,
  footer,
}: {
  eyebrow: string
  title: string
  intro?: string
  children: ReactNode
  footer?: ReactNode
}) {
  return (
    <div className="flex min-h-dvh flex-col bg-ink-950">
      <header
        className="px-4 pb-2"
        style={{ paddingTop: 'calc(env(safe-area-inset-top) + 12px)' }}
      >
        <div className="mx-auto max-w-sm">
          <Link
            to="/"
            aria-label="Назад към началото"
            className="tap -ml-2 flex h-12 w-12 items-center justify-center rounded-xl text-chalk-300 active:bg-ink-800"
          >
            <Icon name="chevronLeft" size={22} />
          </Link>
        </div>
      </header>

      <main className="flex-1 px-6 pb-10">
        <div className="mx-auto w-full max-w-sm">
          <p className="label-micro">{eyebrow}</p>
          <h1 className="mt-2 font-display text-4xl leading-none font-bold tracking-tight uppercase">
            {title}
          </h1>
          {intro && <p className="mt-3 text-sm leading-relaxed text-chalk-500">{intro}</p>}

          <div className="mt-8">{children}</div>

          {footer && <div className="mt-6">{footer}</div>}
        </div>
      </main>
    </div>
  )
}
