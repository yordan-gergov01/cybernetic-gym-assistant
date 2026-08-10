import { useState, type SubmitEvent } from 'react'
import { Field, TextInput } from '../../components/ui'
import { useAuth } from './useAuth'
import { useAuthSubmit } from './useAuthSubmit'

export function RegisterForm() {
  const { register } = useAuth()
  const { busy, message, fields, run } = useAuthSubmit()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const invalid = (field: string) => fields.includes(field)

  function onSubmit(event: SubmitEvent) {
    event.preventDefault()
    void run(() => register(email, password, name))
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4" noValidate>
      <Field label="Име" htmlFor="name">
        <TextInput
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          autoComplete="name"
          invalid={invalid('name')}
          placeholder="Как да те наричаме"
        />
      </Field>

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
          invalid={invalid('email')}
        />
      </Field>

      <Field label="Парола" htmlFor="password" hint="Поне 8 символа.">
        <TextInput
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
          invalid={invalid('password')}
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
        {busy ? 'Създаваме профила…' : 'Създай профил'}
      </button>
    </form>
  )
}
