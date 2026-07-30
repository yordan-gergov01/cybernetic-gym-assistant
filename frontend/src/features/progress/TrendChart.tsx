import type { WeightTrend } from '../../types/api'

type Point = NonNullable<WeightTrend['trend_points']>[number]

/**
 * Weight trend as inline SVG - no chart library. It is one smoothed line plus the raw
 * daily dots; shipping a charting dependency for that would be dead weight in a
 * phone-first bundle.
 */
export function TrendChart({ points, height = 130 }: { points: Point[]; height?: number }) {
  if (points.length < 2) {
    return <p className="py-10 text-center text-sm text-chalk-500">Малко данни за графика.</p>
  }

  const WIDTH = 320
  const PAD_X = 6
  const PAD_Y = 14

  const values = points.flatMap((p) => [p.ewma, p.raw])
  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || 1

  const x = (i: number) => PAD_X + (i * (WIDTH - PAD_X * 2)) / (points.length - 1)
  const y = (v: number) => PAD_Y + (1 - (v - min) / span) * (height - PAD_Y * 2)

  const line = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(p.ewma).toFixed(1)}`).join(' ')
  const area = `${line} L${x(points.length - 1).toFixed(1)},${height} L${x(0).toFixed(1)},${height} Z`
  const last = points[points.length - 1]

  return (
    <svg viewBox={`0 0 ${WIDTH} ${height}`} className="w-full" role="img" aria-label="Графика на теглото">
      <defs>
        <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--color-volt-500)" stopOpacity="0.3" />
          <stop offset="100%" stopColor="var(--color-volt-500)" stopOpacity="0" />
        </linearGradient>
      </defs>

      <path d={area} fill="url(#trendFill)" />
      {points.map((p, i) => (
        <circle key={i} cx={x(i)} cy={y(p.raw)} r="1.8" fill="var(--color-ink-600)" />
      ))}
      <path
        d={line}
        fill="none"
        stroke="var(--color-volt-500)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={x(points.length - 1)} cy={y(last.ewma)} r="4.5" fill="var(--color-volt-400)" />
      <circle cx={x(points.length - 1)} cy={y(last.ewma)} r="9" fill="var(--color-volt-400)" opacity="0.18" />
    </svg>
  )
}
