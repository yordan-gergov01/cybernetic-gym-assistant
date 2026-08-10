import type { InputHTMLAttributes } from 'react'

/** Single-line text input.
 *
 *  `invalid` only paints the border - the sentence explaining what is wrong comes from
 *  the API and is rendered once by the form, so the user is never told the same thing
 *  three times in three colours. */
export function TextInput({
  invalid = false,
  className = '',
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { invalid?: boolean }) {
  return (
    <input
      {...props}
      aria-invalid={invalid || undefined}
      className={`input ${invalid ? 'border-danger-400' : ''} ${className}`}
    />
  )
}
