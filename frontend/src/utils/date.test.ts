import { describe, expect, it } from 'vitest'
import { secondsSince, secondsUntil } from './date'

/** The rest countdown is computed from a deadline and the current clock rather than
 *  counted down, because a phone locks its screen between sets and a suspended interval
 *  comes back with the wrong number. This is the arithmetic that makes that work. */
describe('secondsUntil', () => {
  it('reports the whole seconds still to run', () => {
    expect(secondsUntil(60_000, 0)).toBe(60)
    expect(secondsUntil(60_000, 30_000)).toBe(30)
  })

  it('never goes negative once the deadline has passed', () => {
    expect(secondsUntil(60_000, 90_000)).toBe(0)
  })

  it('still reads one while part of a second is left', () => {
    // Rounding down here would show 0 with the rest not over.
    expect(secondsUntil(60_000, 59_600)).toBe(1)
  })

  it('returns the real remainder after the screen was locked for a while', () => {
    expect(secondsUntil(180_000, 175_000)).toBe(5)
    expect(secondsUntil(180_000, 400_000)).toBe(0)
  })
})

describe('secondsSince', () => {
  it('counts whole elapsed seconds', () => {
    expect(secondsSince(0, 90_900)).toBe(90)
  })

  it('is zero before any time has passed', () => {
    expect(secondsSince(1_000, 1_000)).toBe(0)
    expect(secondsSince(2_000, 1_000)).toBe(0)
  })
})
