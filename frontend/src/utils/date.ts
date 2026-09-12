/** Date helpers. The API speaks ISO dates (YYYY-MM-DD) everywhere. */
import { MONTHS_BG, WEEKDAYS_BG, WEEKDAYS_SHORT_BG } from '../constants/calendar'

/** Today in the user's local timezone - not UTC, or logging after 02:00 lands on the wrong day. */
export const todayIso = (): string => {
  const now = new Date()
  const offsetMs = now.getTimezoneOffset() * 60_000
  return new Date(now.getTime() - offsetMs).toISOString().slice(0, 10)
}


/** Whole seconds left until `deadline`, never negative.
 *
 *  Rounded up, so something with 0.4s to run still reads 1: a countdown that shows 0
 *  while it is still running is the one number it must not get wrong. */
export const secondsUntil = (deadlineMs: number, nowMs: number = Date.now()): number =>
  Math.max(0, Math.ceil((deadlineMs - nowMs) / 1000))

/** Whole seconds elapsed since `start`, floored - 90.9s of work is 90 whole seconds. */
export const secondsSince = (startMs: number, nowMs: number = Date.now()): number =>
  Math.max(0, Math.floor((nowMs - startMs) / 1000))


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

/** "Чт 30" - the label on a day chip, short enough that a week fits across a phone. */
export const formatDayChip = (iso: string): string => {
  const d = new Date(`${iso}T00:00:00`)
  return `${WEEKDAYS_SHORT_BG[d.getDay()]} ${d.getDate()}`
}

/** The `count` days ending today, oldest first. */
export const recentDays = (count: number, from: string = todayIso()): string[] => {
  const end = new Date(`${from}T00:00:00`)
  return Array.from({ length: count }, (_, i) => {
    const d = new Date(end)
    d.setDate(end.getDate() - (count - 1 - i))
    const offsetMs = d.getTimezoneOffset() * 60_000
    return new Date(d.getTime() - offsetMs).toISOString().slice(0, 10)
  })
}
