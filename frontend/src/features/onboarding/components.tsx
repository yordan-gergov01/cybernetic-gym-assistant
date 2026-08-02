import { useState, type ReactNode } from 'react'
import { Icon } from '../../components/ui'
import { isPartialDecimal, isPartialInteger, parseDecimal, parseInteger } from '../../utils/number'
import type { Option } from './constants'

/** Shared frame for every wizard step: one question, an explainer that says why we
 *  ask, then the inputs. The explainer is not decoration - it is what makes people
 *  answer accurately instead of guessing. */
export function StepLayout({
  title,
  explainer,
  children,
}: {
  title: string
  explainer?: string
  children: ReactNode
}) {
  return (
    <div>
      <h2 className="font-display text-2xl leading-tight font-semibold tracking-wide">{title}</h2>
      {explainer && <p className="mt-2 text-sm leading-relaxed text-chalk-500">{explainer}</p>}
      <div className="mt-6 space-y-3">{children}</div>
    </div>
  )
}

/** Big tappable choice card - never a native select, which is unusable one-handed. */
export function OptionCard({
  option,
  selected,
  onSelect,
}: {
  option: Option
  selected: boolean
  onSelect: () => void
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={`tap flex w-full items-start gap-3 rounded-2xl border p-4 text-left ${
        selected ? 'border-volt-500 bg-volt-500/10' : 'border-ink-700 bg-ink-800'
      }`}
    >
      <span
        className={`mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full border-2 ${
          selected ? 'border-volt-500 bg-volt-500 text-ink-950' : 'border-ink-600'
        }`}
      >
        {selected && <Icon name="check" size={12} />}
      </span>
      <span className="min-w-0">
        <span className={`block font-semibold ${selected ? 'text-chalk-50' : 'text-chalk-50'}`}>
          {option.label}
        </span>
        {option.hint && <span className="mt-0.5 block text-sm text-chalk-500">{option.hint}</span>}
      </span>
    </button>
  )
}

/** Multi-select chip, used for muscle groups and dietary tags. */
export function Chip({
  label,
  selected,
  onToggle,
  disabled,
}: {
  label: string
  selected: boolean
  onToggle: () => void
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={disabled && !selected}
      aria-pressed={selected}
      className={`tap min-h-11 rounded-xl border px-4 text-sm font-medium disabled:opacity-35 ${
        selected ? 'border-volt-500 bg-volt-500 text-ink-950' : 'border-ink-700 bg-ink-800 text-chalk-300'
      }`}
    >
      {label}
    </button>
  )
}

export function Field({
  label,
  hint,
  children,
}: {
  label: string
  hint?: string
  children: ReactNode
}) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
      {hint && <p className="mt-1.5 text-xs text-chalk-500">{hint}</p>}
    </div>
  )
}

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

export function NumberField({
  label,
  value,
  onChange,
  unit,
  placeholder,
  hint,
  integer = false,
}: {
  label: string
  value: number | undefined
  onChange: (value: number | undefined) => void
  unit?: string
  placeholder?: string
  hint?: string
  integer?: boolean
}) {
  return (
    <Field label={label} hint={hint}>
      <div className="relative">
        <NumericInput
          value={value}
          onChange={onChange}
          integer={integer}
          placeholder={placeholder}
          className="input num pr-12 text-lg font-semibold"
        />
        {unit && (
          <span className="absolute top-1/2 right-4 -translate-y-1/2 text-sm text-chalk-500">{unit}</span>
        )}
      </div>
    </Field>
  )
}

export function TextField({
  label,
  value,
  onChange,
  placeholder,
  hint,
  rows = 3,
}: {
  label: string
  value: string | undefined
  onChange: (value: string) => void
  placeholder?: string
  hint?: string
  rows?: number
}) {
  return (
    <Field label={label} hint={hint}>
      <textarea
        className="input min-h-0 resize-none py-3 leading-relaxed"
        rows={rows}
        placeholder={placeholder}
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
      />
    </Field>
  )
}
