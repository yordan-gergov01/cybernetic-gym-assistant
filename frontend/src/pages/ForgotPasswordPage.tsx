import { useState, type SubmitEvent } from 'react'
import { Link } from 'react-router-dom'
import { Callout, Field, TextInput } from '../components/ui'
import { authApi } from '../features/auth/api'
import { AuthLayout } from '../features/auth/AuthLayout'
import { useAuthSubmit } from '../features/auth/useAuthSubmit'

/**
 * Asks for the address and stops there.
 *
 * The answer is deliberately the same whether or not the address is registered, so this
 * screen never says "no such account" - it would turn the form into a way of finding out
 * who has one.
 */
export function ForgotPasswordPage() {
  const { busy, message, fields, run } = useAuthSubmit()
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState<string | null>(null)

  function onSubmit(event: SubmitEvent) {
    event.preventDefault()
    void run(async () => {
      const answer = await authApi.forgotPassword(email)
      setSent(answer.detail)
    })
  }

  return (
    <AuthLayout
      eyebrow="Забравена парола"
      title="Нова парола"
      intro={
        sent
          ? undefined
          : 'Въведи имейла на профила си. Ще получиш линк, с който да зададеш нова парола.'
      }
      footer={
        <p className="text-center text-sm text-chalk-500">
          Сети ли се?{' '}
          <Link to="/login" className="font-semibold text-volt-400">
            Влез
          </Link>
        </p>
      }
    >
      {sent ? (
        <Callout tone="ok" title="Провери пощата си">
          {sent}
        </Callout>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <Field label="Имейл" htmlFor="email">
            <TextInput
              id="email"
              type="email"
              inputMode="email"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              invalid={fields.includes('email')}
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
            {busy ? 'Изпращаме…' : 'Изпрати линк'}
          </button>
        </form>
      )}
    </AuthLayout>
  )
}
