import type { ReactNode } from 'react'

/** A labelled number inside its own surface: calories, TDEE, yesterday's tonnage.
 *
 *  The caption is set above the value rather than below it, so the eye lands on the
 *  number last and stays there — the number is what the user came for. */
export function StatBox({
  label,
  value,
  unit,
  footer,
  size = 'md',
}: {
  label: string
  value: ReactNode
  unit?: string
  footer?: ReactNode
  size?: 'md' | 'lg'
}) {
  return (
    <div className="rounded-2xl border border-ink-700 bg-ink-900 p-4">
      <p className="label-micro">{label}</p>
      <p className="mt-2 flex items-baseline gap-1.5">
        <span className={size === 'lg' ? 'stat' : 'stat-sm'}>{value}</span>
        {unit && <span className="text-sm text-chalk-500">{unit}</span>}
      </p>
      {footer && <div className="mt-2 text-xs text-chalk-500">{footer}</div>}
    </div>
  )
}
