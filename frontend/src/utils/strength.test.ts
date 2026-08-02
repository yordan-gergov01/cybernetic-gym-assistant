import { describe, expect, it } from 'vitest'
import { estimate1RM } from './strength'

describe('estimate1RM', () => {
  it('treats a single rep as the max itself', () => {
    expect(estimate1RM(100, 1)).toBe(100)
  })

  it('estimates a higher max the more reps were done with the same weight', () => {
    expect(estimate1RM(100, 5)).toBeGreaterThan(estimate1RM(100, 3))
    expect(estimate1RM(100, 3)).toBeGreaterThan(estimate1RM(100, 1))
  })

  it('estimates a higher max for more weight at the same reps', () => {
    expect(estimate1RM(105, 5)).toBeGreaterThan(estimate1RM(100, 5))
  })

  it('agrees with the backend Epley formula (weight * (1 + reps / 30))', () => {
    // 100 kg x 10 -> 133.3 kg, the value calculate_1rm() returns for the same set.
    expect(estimate1RM(100, 10)).toBe(133.3)
  })

  it('rounds to one decimal so the wizard never shows a float tail', () => {
    const shown = String(estimate1RM(82.5, 7))
    expect(shown.split('.')[1]?.length ?? 0).toBeLessThanOrEqual(1)
  })
})
