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

/** "преди 2 ч", "вчера" — coarse on purpose: the exact minute never matters here. */
export const formatRelativeTime = (isoTimestamp: string): string => {
  const then = new Date(isoTimestamp)
  const minutes = Math.round((Date.now() - then.getTime()) / 60_000)
  if (minutes < 1) return 'сега'
  if (minutes < 60) return `преди ${minutes} мин`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `преди ${hours} ч`
  const days = Math.round(hours / 24)
  if (days === 1) return 'вчера'
  if (days < 7) return `преди ${days} дни`
  return formatShortDate(isoTimestamp.slice(0, 10))
}

export const formatShortDate = (iso: string): string => {
  const d = new Date(`${iso}T00:00:00`)
  return `${d.getDate()}.${d.getMonth() + 1}`
}
