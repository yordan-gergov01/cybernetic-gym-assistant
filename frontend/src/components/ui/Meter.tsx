import { clampPercent } from '../../utils/format'

const TONE_CLASS = {
  accent: 'bg-volt-500',
  ok: 'bg-ok-400',
  warn: 'bg-warn-400',
  danger: 'bg-danger-400',
} as const

/** Horizontal progress bar for macro / calorie completion. */
export function Meter({
  value,
  max,
  tone = 'accent',
  size = 'sm',
}: {
  value: number
  max: number
  tone?: keyof typeof TONE_CLASS
  /** Thickness carries importance: calories read heaviest, protein next. */
  size?: 'sm' | 'md' | 'lg'
}) {
  const height = size === 'lg' ? 'h-3' : size === 'md' ? 'h-2.5' : 'h-1.5'
  return (
    <div className={`${height} w-full overflow-hidden rounded-full bg-ink-700`}>
      <div
        className={`h-full rounded-full ${TONE_CLASS[tone]} transition-[width] duration-500`}
        style={{ width: `${clampPercent(value, max)}%` }}
      />
    </div>
  )
}
