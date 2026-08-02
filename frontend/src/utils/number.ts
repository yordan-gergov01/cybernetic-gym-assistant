/** Parsing of numbers the user typed.
 *
 *  A Bulgarian keyboard puts a comma on the decimal key, so every field that takes a
 *  decimal accepts both separators - a body weight of 82,4 must not be lost just
 *  because the phone offered a comma. */

const DECIMAL_INPUT = /^\d*[.,]?\d*$/
const INTEGER_INPUT = /^\d*$/

/** True while the text is still on its way to a number ("10." before "10.5").
 *  Used to reject stray characters as they are typed, not to validate the result. */
export const isPartialDecimal = (raw: string): boolean => DECIMAL_INPUT.test(raw)
export const isPartialInteger = (raw: string): boolean => INTEGER_INPUT.test(raw)

/** The number the text represents, or undefined while it represents none ("", "12,"). */
export const parseDecimal = (raw: string): number | undefined => {
  const normalized = raw.trim().replace(',', '.')
  if (normalized === '') return undefined
  const value = Number(normalized)
  return Number.isFinite(value) ? value : undefined
}

/** Reps, sets and years are counts - a fractional one means nothing. */
export const parseInteger = (raw: string): number | undefined => {
  const value = parseDecimal(raw)
  return value === undefined ? undefined : Math.trunc(value)
}
