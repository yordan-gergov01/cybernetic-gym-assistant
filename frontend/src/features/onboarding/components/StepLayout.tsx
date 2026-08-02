import type { ReactNode } from 'react'

/** Shared frame for every wizard step: one question, an explainer that says why we
 *  ask, then the inputs. The explainer is not decoration - it is what makes people
 *  answer accurately instead of guessing. */
export function StepLayout({
  title,
  explainer,
  children,
}: {
  title: string
  explainer?: string
  children: ReactNode
}) {
  return (
    <div>
      <h2 className="font-display text-2xl leading-tight font-semibold tracking-wide">{title}</h2>
      {explainer && <p className="mt-2 text-sm leading-relaxed text-chalk-500">{explainer}</p>}
      <div className="mt-6 space-y-3">{children}</div>
    </div>
  )
}
