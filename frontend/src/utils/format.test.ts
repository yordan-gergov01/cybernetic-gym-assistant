import { describe, expect, it } from 'vitest'
import { formatClock } from './format'

describe('formatClock', () => {
  it('pads both halves so a running clock does not change width', () => {
    expect(formatClock(9)).toBe('00:09')
    expect(formatClock(65)).toBe('01:05')
    expect(formatClock(600)).toBe('10:00')
  })

  it('keeps counting past an hour rather than wrapping', () => {
    // A long session is still one session; "00:05" for 65 minutes would be a lie.
    expect(formatClock(3_905)).toBe('65:05')
  })
})
