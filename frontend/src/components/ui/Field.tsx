import type { ReactNode } from 'react'

/** Label, control, and the hint that explains why we ask.
 *
 *  An error replaces the hint rather than stacking under it: once something is wrong,
 *  the fix is the only thing worth reading. */
export function Field({
  label,
  hint,
  error,
  htmlFor,
  children,
}: {
  label: string
  hint?: string
  error?: string
  htmlFor?: string
  children: ReactNode
}) {
  return (
    <div>
      <label className="label-micro mb-2 block" htmlFor={htmlFor}>
        {label}
      </label>
      {children}
      {error ? (
        <p className="mt-1.5 text-xs text-danger-400">{error}</p>
      ) : (
        hint && <p className="mt-1.5 text-xs text-chalk-500">{hint}</p>
      )}
    </div>
  )
}
