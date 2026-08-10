/** Tiny inline trend line for one exercise's estimated max.
 *
 *  Shape only — no axes, no labels. The number next to it carries the value; this just
 *  says whether the last few weeks went up, flat or down at a glance. */
export function Sparkline({
  points,
  width = 56,
  height = 24,
}: {
  points: number[]
  width?: number
  height?: number
}) {
  if (points.length < 2) return null

  const min = Math.min(...points)
  const max = Math.max(...points)
  const span = max - min || 1
  const step = width / (points.length - 1)

  const path = points
    .map((value, i) => {
      const x = i * step
      const y = height - ((value - min) / span) * height
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')

  return (
    <svg width={width} height={height} className="shrink-0" aria-hidden="true">
      <path
        d={path}
        fill="none"
        stroke="var(--color-volt-500)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
