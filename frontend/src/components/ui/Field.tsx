import type { ReactNode } from 'react'

/** Label, control, and the hint that explains why we ask. */
export function Field({
  label,
  hint,
  children,
}: {
  label: string
  hint?: string
  children: ReactNode
}) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
      {hint && <p className="mt-1.5 text-xs text-chalk-500">{hint}</p>}
    </div>
  )
}
