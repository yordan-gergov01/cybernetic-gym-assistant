/** Date helpers. The API speaks ISO dates (YYYY-MM-DD) everywhere. */

/** Today in the user's local timezone - not UTC, or logging after 02:00 lands on the wrong day. */
export const todayIso = (): string => {
  const now = new Date()
  const offsetMs = now.getTimezoneOffset() * 60_000
  return new Date(now.getTime() - offsetMs).toISOString().slice(0, 10)
}

const WEEKDAYS_BG = ['неделя', 'понеделник', 'вторник', 'сряда', 'четвъртък', 'петък', 'събота']
const MONTHS_BG = [
  'януари', 'февруари', 'март', 'април', 'май', 'юни',
  'юли', 'август', 'септември', 'октомври', 'ноември', 'декември',
]

export const formatDayLabel = (iso: string): string => {
  const d = new Date(`${iso}T00:00:00`)
  return `${WEEKDAYS_BG[d.getDay()]}, ${d.getDate()} ${MONTHS_BG[d.getMonth()]}`
}

export const formatShortDate = (iso: string): string => {
  const d = new Date(`${iso}T00:00:00`)
  return `${d.getDate()}.${d.getMonth() + 1}`
}
