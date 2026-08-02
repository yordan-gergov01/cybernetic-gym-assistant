import { Field } from './Field'

/** Free-text answer. A textarea rather than an input: these answers are sentences
 *  (injuries, unavailable times) and they must be readable while being typed. */
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
