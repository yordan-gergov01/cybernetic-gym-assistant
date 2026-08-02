import { describe, expect, it } from 'vitest'
import { conflictingGoal } from './goal'

describe('conflictingGoal', () => {
  it('recommends cutting first when a man well above 15% wants to bulk or maintain', () => {
    expect(conflictingGoal(22, 'male', 'bulk')).toBe('cut')
    expect(conflictingGoal(22, 'male', 'maintain')).toBe('cut')
  })

  it('leaves the goal alone when it already matches the recommendation', () => {
    expect(conflictingGoal(22, 'male', 'cut')).toBeNull()
    expect(conflictingGoal(22, 'male', 'aggressive_cut')).toBeNull()
  })

  it('recommends bulking when cutting further would go below the healthy floor', () => {
    expect(conflictingGoal(8, 'male', 'cut')).toBe('bulk')
    expect(conflictingGoal(8, 'male', 'aggressive_cut')).toBe('bulk')
    expect(conflictingGoal(15, 'female', 'cut')).toBe('bulk')
  })

  it('holds women to their own thresholds, not the male ones', () => {
    // 22% is above the male cut threshold but inside the optimal range for a woman.
    expect(conflictingGoal(22, 'male', 'bulk')).toBe('cut')
    expect(conflictingGoal(22, 'female', 'bulk')).toBeNull()
    // 15% is below the female floor but comfortable for a man.
    expect(conflictingGoal(15, 'female', 'cut')).toBe('bulk')
    expect(conflictingGoal(15, 'male', 'cut')).toBeNull()
  })

  it('says nothing inside the optimal range, whatever the goal', () => {
    for (const goal of ['bulk', 'cut', 'maintain', 'aggressive_cut'] as const) {
      expect(conflictingGoal(12, 'male', goal)).toBeNull()
    }
  })

  it('stays silent until body fat, sex and goal are all known', () => {
    expect(conflictingGoal(undefined, 'male', 'bulk')).toBeNull()
    expect(conflictingGoal(22, undefined, 'bulk')).toBeNull()
    expect(conflictingGoal(22, 'male', undefined)).toBeNull()
  })
})
