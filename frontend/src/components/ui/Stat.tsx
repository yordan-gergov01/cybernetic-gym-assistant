import type { ReactNode } from 'react'

export type StatTone = 'default' | 'accent' | 'warn' | 'danger' | 'ok'

const TONE_CLASS: Record<StatTone, string> = {
  default: 'text-chalk-50',
  accent: 'text-volt-400',
  warn: 'text-warn-400',
  danger: 'text-danger-400',
  ok: 'text-ok-400',
}

/** Big number + label - the primary way this app presents data. */
export function Stat({
  value,
  unit,
  label,
  tone = 'default',
  size = 'lg',
}: {
  value: ReactNode
  unit?: string
  label: string
  tone?: StatTone
  size?: 'lg' | 'sm'
}) {
  return (
    <div>
      <div className={`${size === 'lg' ? 'stat' : 'stat-sm'} ${TONE_CLASS[tone]}`}>
        {value}
        {unit && <span className="ml-1 text-base font-semibold text-chalk-500">{unit}</span>}
      </div>
      <div className="mt-1.5 text-[10px] font-semibold tracking-[0.12em] text-chalk-500 uppercase">{label}</div>
    </div>
  )
}
