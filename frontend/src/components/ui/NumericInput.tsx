import { useState } from 'react'
import { isPartialDecimal, isPartialInteger, parseDecimal, parseInteger } from '../../utils/number'

/** Numeric input that keeps what the user actually typed.
 *
 *  The text on screen is owned by the field, not derived from the parsed number:
 *  re-rendering the parse result turns "10." back into "10" mid-keystroke and makes a
 *  decimal impossible to enter. The parsed value is reported upward, the half-finished
 *  text stays put. Characters that could never belong to a number are rejected instead
 *  of being shown and silently parsed away.
 *
 *  The initial text comes from the value once, on mount - wizard steps mount with the
 *  draft already loaded and nothing rewrites these fields from the outside. */
export function NumericInput({
  value,
  onChange,
  integer = false,
  placeholder,
  className = '',
  ariaLabel,
}: {
  value: number | undefined
  onChange: (value: number | undefined) => void
  integer?: boolean
  placeholder?: string
  className?: string
  ariaLabel?: string
}) {
  const [text, setText] = useState(() => (value === undefined ? '' : String(value)))

  return (
    <input
      inputMode={integer ? 'numeric' : 'decimal'}
      aria-label={ariaLabel}
      className={className}
      placeholder={placeholder}
      value={text}
      onChange={(e) => {
        const raw = e.target.value
        if (!(integer ? isPartialInteger(raw) : isPartialDecimal(raw))) return
        setText(raw)
        onChange(integer ? parseInteger(raw) : parseDecimal(raw))
      }}
    />
  )
}
