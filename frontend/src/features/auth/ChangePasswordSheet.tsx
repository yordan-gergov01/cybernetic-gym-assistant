import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { ErrorNote, Field, Sheet, TextInput } from '../../components/ui'
import { MIN_PASSWORD_LENGTH, PASSWORD_HINT_BG } from '../../constants/auth'
import { showToast } from '../../services/toast'
import { authApi } from './api'

/** Changing the password from inside the account.
 *
 *  The current password is asked for even though the session already proves who this is:
 *  the realistic attacker is a phone left unlocked on a bench, and that phone does not
 *  know the old password. */
export function ChangePasswordSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [tooShort, setTooShort] = useState(false)

  const change = useMutation({
    // The sheet covers the bottom of the screen, where a toast would appear.
    meta: { inlineError: true },
    mutationFn: () => authApi.changePassword(current, next),
    onSuccess: (answer) => {
      showToast(answer.detail, 'ok')
      close()
    },
  })

  function close() {
    setCurrent('')
    setNext('')
    setTooShort(false)
    change.reset()
    onClose()
  }

  return (
    <Sheet open={open} onClose={close} title="Смяна на паролата">
      <div className="space-y-4">
        <Field label="Текуща парола" htmlFor="current-password">
          <TextInput
            id="current-password"
            type="password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            autoComplete="current-password"
          />
        </Field>

        <Field label={`Нова парола (${PASSWORD_HINT_BG.toLowerCase()})`} htmlFor="new-password">
          <TextInput
            id="new-password"
            type="password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            autoComplete="new-password"
            invalid={tooShort}
          />
        </Field>

        {tooShort && (
          <p role="alert" className="text-sm text-danger-400">
            Новата парола трябва да е поне {MIN_PASSWORD_LENGTH} знака.
          </p>
        )}
        {change.error && <ErrorNote error={change.error} />}

        <button
          type="button"
          disabled={change.isPending || !current || !next}
          onClick={() => {
            // Checked before the request so a too-short password comes back as one
            // sentence about the field, not as a schema error.
            if (next.length < MIN_PASSWORD_LENGTH) {
              setTooShort(true)
              return
            }
            setTooShort(false)
            change.mutate()
          }}
          className="btn-primary w-full"
        >
          {change.isPending ? 'Сменяме…' : 'Смени паролата'}
        </button>
      </div>
    </Sheet>
  )
}
