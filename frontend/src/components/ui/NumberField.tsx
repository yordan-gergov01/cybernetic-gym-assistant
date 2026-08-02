import { Field } from './Field'
import { NumericInput } from './NumericInput'

/** Labelled numeric field with the unit pinned inside the input. */
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
