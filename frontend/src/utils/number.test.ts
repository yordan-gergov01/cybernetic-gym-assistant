import { describe, expect, it } from 'vitest'
import { isPartialDecimal, isPartialInteger, parseDecimal, parseInteger } from './number'

describe('parseDecimal', () => {
  it('reads a comma as a decimal separator, like the Bulgarian keyboard produces', () => {
    expect(parseDecimal('82,4')).toBe(parseDecimal('82.4'))
  })

  it('reports no value for text that is not a number yet, instead of a wrong one', () => {
    // "82," on the way to "82,5": reporting 82 here would save a weight the user
    // never entered.
    for (const halfTyped of ['', ' ', ',', '.', 'abc']) {
      expect(parseDecimal(halfTyped)).toBeUndefined()
    }
  })

  it('keeps a trailing separator harmless - the number so far is what counts', () => {
    expect(parseDecimal('10.')).toBe(10)
    expect(parseDecimal('10,')).toBe(10)
  })

  it('distinguishes an empty field from a zero', () => {
    expect(parseDecimal('')).toBeUndefined()
    expect(parseDecimal('0')).toBe(0)
  })
})

describe('parseInteger', () => {
  it('never yields a fractional count - reps and years are whole', () => {
    expect(Number.isInteger(parseInteger('12,7'))).toBe(true)
    expect(Number.isInteger(parseInteger('3.9'))).toBe(true)
  })

  it('passes an empty field through as no value', () => {
    expect(parseInteger('')).toBeUndefined()
  })
})

describe('accepting keystrokes', () => {
  it('lets a decimal be typed one character at a time', () => {
    // Every prefix of "82,5" must survive, or the separator is eaten mid-entry and a
    // decimal becomes impossible to enter at all.
    for (const prefix of ['8', '82', '82,', '82,5']) {
      expect(isPartialDecimal(prefix)).toBe(true)
    }
  })

  it('rejects text that can never become a number', () => {
    for (const junk of ['abc', '1.2.3', '1,2,3', '-5', '1e5']) {
      expect(isPartialDecimal(junk)).toBe(false)
    }
  })

  it('refuses a separator where only whole numbers make sense', () => {
    expect(isPartialInteger('12')).toBe(true)
    expect(isPartialInteger('12,')).toBe(false)
    expect(isPartialInteger('12.5')).toBe(false)
  })
})
