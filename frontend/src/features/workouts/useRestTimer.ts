import { useCallback, useEffect, useRef, useState } from 'react'
import { secondsSince, secondsUntil } from '../../utils/date'

export const REST_EXTENSION_SECONDS = 30

/** The rest between sets.
 *
 *  Time is kept as a deadline and recomputed from the clock on every tick, instead of
 *  counting a number down. A phone in a gym locks its screen between sets, and browsers
 *  throttle or suspend timers in a hidden tab: a decrementing counter comes back wrong,
 *  a deadline comes back right.
 */
export function useRestTimer() {
  const [deadline, setDeadline] = useState<number | null>(null)
  const [total, setTotal] = useState(0)
  const [remaining, setRemaining] = useState(0)
  // Vibrating whenever a render finds zero would buzz once per tick.
  const buzzed = useRef(false)

  useEffect(() => {
    if (deadline === null) return

    const tick = () => {
      const left = secondsUntil(deadline)
      setRemaining(left)
      if (left === 0 && !buzzed.current) {
        buzzed.current = true
        // A phone between sets is in a pocket, not being looked at. Vibration is absent
        // on desktop and on iOS Safari, so it can only ever be a bonus cue.
        if ('vibrate' in navigator) navigator.vibrate([200, 100, 200])
      }
    }

    tick()
    const id = setInterval(tick, 500)
    return () => clearInterval(id)
  }, [deadline])

  const start = useCallback((seconds: number) => {
    if (seconds <= 0) return
    buzzed.current = false
    setTotal(seconds)
    setDeadline(Date.now() + seconds * 1000)
  }, [])

  const extend = useCallback(() => {
    setDeadline((current) => (current === null ? null : current + REST_EXTENSION_SECONDS * 1000))
    setTotal((current) => current + REST_EXTENSION_SECONDS)
    buzzed.current = false
  }, [])

  const skip = useCallback(() => {
    setDeadline(null)
    setRemaining(0)
  }, [])

  return {
    /** null while no rest is running; the countdown is only rendered when it is. */
    remaining: deadline === null ? null : remaining,
    total,
    start,
    extend,
    skip,
  }
}

/** How long the session has been going, for the header clock. */
export function useElapsedSeconds(): number {
  const startedAt = useRef(Date.now())
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const tick = () => setElapsed(secondsSince(startedAt.current))
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [])

  return elapsed
}
