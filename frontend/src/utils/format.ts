/** Formatting helpers. Kept here so screens never inline number/locale logic. */

/** Weights: one decimal, but only when it carries information (82.5 vs 80). */
export const formatWeight = (kg: number | null | undefined): string => {
  if (kg === null || kg === undefined) return '-'
  return Number.isInteger(kg) ? String(kg) : kg.toFixed(1)
}

export const formatKcal = (value: number | null | undefined): string =>
  value === null || value === undefined ? '-' : String(Math.round(value))

export const formatGrams = (value: number | null | undefined): string =>
  value === null || value === undefined ? '-' : String(Math.round(value))

/** Signed rate, e.g. "-0.35" - the sign is the point, so it is always shown. */
export const formatRate = (kgPerWeek: number | null | undefined): string =>
  kgPerWeek === null || kgPerWeek === undefined ? '-' : `${kgPerWeek > 0 ? '+' : ''}${kgPerWeek.toFixed(2)}`

export const formatDelta = (value: number | null | undefined): string =>
  value === null || value === undefined ? '-' : `${value > 0 ? '+' : ''}${Math.round(value)}`

export const clampPercent = (value: number, max: number): number =>
  max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0
