import { useState, type SubmitEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Callout, Field, TextInput } from '../components/ui'
import { PASSWORD_HINT_BG } from '../constants/auth'
import { AuthLayout } from '../features/auth/AuthLayout'
import { useAuth } from '../features/auth/useAuth'
import { useAuthSubmit } from '../features/auth/useAuthSubmit'

/**
 * The screen the emailed link opens.
 *
 * A successful reset signs the user straight in - the token proved they own the mailbox,
 * and sending them to a login form to retype the password they just chose would be
 * theatre. The router takes over from there, so this component renders nothing after it.
 */
export function ResetPasswordPage() {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const { resetPassword } = useAuth()
  const { busy, message, fields, run } = useAuthSubmit()

  const [password, setPassword] = useState('')
  const [repeat, setRepeat] = useState('')
  const [mismatch, setMismatch] = useState(false)

  function onSubmit(event: SubmitEvent) {
    event.preventDefault()
    // Checked here rather than by the API: the second field exists to catch a typo in
    // the first, and only this screen knows what was typed in it.
    if (password !== repeat) {
      setMismatch(true)
      return
    }
    setMismatch(false)
    void run(() => resetPassword(token, password))
  }

  if (!token) {
    return (
      <AuthLayout eyebrow="Нова парола" title="Линкът е непълен">
        <Callout tone="danger" title="Липсва код">
          Отвори линка от имейла цял - в него има код, без който паролата не може да се
          смени.
        </Callout>
        <Link to="/forgot-password" className="btn-outline mt-4 w-full">
          Заяви нов линк
        </Link>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout
      eyebrow="Нова парола"
      title="Задай парола"
      intro={`${PASSWORD_HINT_BG}. След това те влизаме в профила направо.`}
      footer={
        <p className="text-center text-sm text-chalk-500">
          Изтекъл линк?{' '}
          <Link to="/forgot-password" className="font-semibold text-volt-400">
            Заяви нов
          </Link>
        </p>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <Field label="Нова парола" htmlFor="password">
          <TextInput
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            invalid={fields.includes('new_password')}
          />
        </Field>

        <Field label="Повтори паролата" htmlFor="repeat">
          <TextInput
            id="repeat"
            type="password"
            value={repeat}
            onChange={(e) => setRepeat(e.target.value)}
            autoComplete="new-password"
            invalid={mismatch}
          />
        </Field>

        {(mismatch || message) && (
          <p
            role="alert"
            className="rounded-xl border border-danger-400/40 bg-danger-400/10 px-4 py-3 text-sm leading-relaxed text-danger-400"
          >
            {mismatch ? 'Двете полета не съвпадат.' : message}
          </p>
        )}

        <button type="submit" className="btn-primary w-full" disabled={busy}>
          {busy ? 'Запазваме…' : 'Запази и влез'}
        </button>
      </form>
    </AuthLayout>
  )
}
