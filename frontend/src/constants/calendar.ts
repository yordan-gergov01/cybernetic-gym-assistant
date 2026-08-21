/** Bulgarian calendar names, together in one file.
 *
 *  They lived in two modules in two different shapes and drifted apart: the date helpers
 *  index by `Date.getDay()` (Sunday first), while the week strip is a fixed Monday-first
 *  header. Both are here so it is visible that they describe the same seven days. */

/** Indexed by `Date.getDay()` — index 0 is Sunday. */
export const WEEKDAYS_BG = [
  'неделя',
  'понеделник',
  'вторник',
  'сряда',
  'четвъртък',
  'петък',
  'събота',
] as const

/** Indexed by `Date.getDay()`, for a day chip: "Чт 30". */
export const WEEKDAYS_SHORT_BG = ['Нд', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'] as const

/** The header of the week strip, which always starts on Monday because the training
 *  week does. Not indexed by `getDay()` - it is a fixed row of seven labels. */
export const WEEK_STRIP_LABELS = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'НД'] as const

export const MONTHS_BG = [
  'януари',
  'февруари',
  'март',
  'април',
  'май',
  'юни',
  'юли',
  'август',
  'септември',
  'октомври',
  'ноември',
  'декември',
] as const
