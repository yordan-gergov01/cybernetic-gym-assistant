import type { ReactNode } from 'react'

export type CalloutTone = 'accent' | 'ok' | 'warn' | 'danger'

/** Tinted, bordered panel for a verdict the user must not scroll past: "on track",
 *  "no weigh-in today", "this estimate is uncertain".
 *
 *  Tone carries meaning, so it is never chosen for looks — and never alone: every
 *  caller pairs it with a title that says the same thing in words, for anyone who
 *  cannot separate the colours. */
const TONES: Record<CalloutTone, string> = {
  accent: 'border-volt-500/40 bg-volt-500/10',
  ok: 'border-ok-400/40 bg-ok-400/10',
  warn: 'border-warn-400/40 bg-warn-400/10',
  danger: 'border-danger-400/40 bg-danger-400/10',
}

const TITLE_TONES: Record<CalloutTone, string> = {
  accent: 'text-volt-400',
  ok: 'text-ok-400',
  warn: 'text-warn-400',
  danger: 'text-danger-400',
}

export function Callout({
  tone = 'accent',
  title,
  children,
  action,
}: {
  tone?: CalloutTone
  title: string
  children?: ReactNode
  action?: ReactNode
}) {
  return (
    <div className={`rounded-2xl border p-4 ${TONES[tone]}`}>
      <p className={`font-display text-sm font-bold tracking-[0.08em] uppercase ${TITLE_TONES[tone]}`}>
        {title}
      </p>
      {children && <div className="mt-2 text-sm leading-relaxed text-chalk-300">{children}</div>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}
