/** Circular progress with the count in the middle — "3/4 тренировки".
 *
 *  An SVG rather than a chart library: it is one arc, and a phone-first bundle should
 *  not carry a charting dependency for it. */
export function Ring({
  value,
  max,
  label,
  size = 128,
}: {
  value: number
  max: number
  label?: string
  size?: number
}) {
  const stroke = 8
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const ratio = max > 0 ? Math.min(1, Math.max(0, value / max)) : 0

  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        className="-rotate-90"
        role="img"
        aria-label={`${value} от ${max}${label ? ` ${label}` : ''}`}
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-ink-700)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-volt-500)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - ratio)}
        />
      </svg>
      <div className="absolute text-center">
        <div className="stat-sm">
          {value}/{max}
        </div>
        {label && <div className="label-micro mt-1">{label}</div>}
      </div>
    </div>
  )
}
