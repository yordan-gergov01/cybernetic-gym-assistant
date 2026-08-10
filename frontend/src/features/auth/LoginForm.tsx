import { useState, type SubmitEvent } from 'react'
import { Field, TextInput } from '../../components/ui'
import { useAuth } from './useAuth'
import { useAuthSubmit } from './useAuthSubmit'

export function LoginForm() {
  const { login } = useAuth()
  const { busy, message, fields, run } = useAuthSubmit()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  function onSubmit(event: SubmitEvent) {
    event.preventDefault()
    void run(() => login(email, password))
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4" noValidate>
      <Field label="Имейл" htmlFor="email">
        <TextInput
          id="email"
          type="email"
          inputMode="email"
          // Phone keyboards capitalise the first letter by default, which silently
          // turns the address into one the user never registered with.
          autoCapitalize="none"
          autoCorrect="off"
          spellCheck={false}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          invalid={fields.includes('email')}
        />
      </Field>

      <Field label="Парола" htmlFor="password">
        <TextInput
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          invalid={fields.includes('password')}
        />
      </Field>

      {message && (
        <p
          role="alert"
          className="rounded-xl border border-danger-400/40 bg-danger-400/10 px-4 py-3 text-sm leading-relaxed text-danger-400"
        >
          {message}
        </p>
      )}

      <button type="submit" className="btn-primary w-full" disabled={busy}>
        {busy ? 'Влизаме…' : 'Влез'}
      </button>
    </form>
  )
}
