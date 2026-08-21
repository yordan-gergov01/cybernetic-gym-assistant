/** How much of the past each screen shows.
 *
 *  These are product decisions, not implementation details: they trade a phone screen's
 *  worth of space against how far back the user can see. Kept together so the answer to
 *  "why four weeks here and thirty days there" is one file rather than five components. */

/** Windows offered for the weight trend. The chart and the rate always describe the same
 *  period, because the window is applied on the backend before the trend is computed.
 *  `days: 0` means everything ever logged. */
export const TREND_RANGES = [
  { label: '1 мес', days: 30 },
  { label: '3 мес', days: 90 },
  { label: '6 мес', days: 180 },
  { label: 'Всичко', days: 0 },
] as const

/** Window for the strength list. Four weeks is long enough for a trend to mean
 *  something and short enough to still describe the current block. */
export const STRENGTH_WEEKS = 4

/** A whole program can carry twenty-odd exercises; the strength list is a summary, not
 *  a ledger, so the rest are counted rather than dropped without a word. */
export const STRENGTH_LIST_VISIBLE = 8

/** Days in the nutrition date strip. Four fits across a phone without scrolling. */
export const NUTRITION_VISIBLE_DAYS = 4

/** How far back the program screen looks for logged sessions. A program is capped at 20
 *  weeks, so this covers a whole one at any realistic frequency. */
export const PROGRAM_LOG_WINDOW = 200
