import { useState } from 'react'
import { ApiError } from '../../services/httpClient'

export type SubmitState = {
  busy: boolean
  message: string | null
  /** Field paths the API rejected, so the inputs can be marked. */
  fields: string[]
  run: (action: () => Promise<unknown>) => Promise<void>
  reset: () => void
}

/** Shared submit handling for the auth forms.
 *
 *  The message always comes from the API - it is already a Bulgarian sentence written
 *  against the actual schema (backend app/core/errors.py), so restating it here would
 *  only make it vaguer. The one case the backend cannot answer is the request never
 *  arriving, which is what the fallback covers. */
export function useAuthSubmit(): SubmitState {
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [fields, setFields] = useState<string[]>([])

  const reset = () => {
    setMessage(null)
    setFields([])
  }

  const run = async (action: () => Promise<unknown>) => {
    reset()
    setBusy(true)
    try {
      await action()
    } catch (error) {
      if (error instanceof ApiError) {
        setMessage(error.message)
        setFields(error.fields)
      } else {
        // fetch only rejects like this when the request never completed.
        setMessage('Няма връзка със сървъра. Провери интернета си и опитай пак.')
      }
    } finally {
      setBusy(false)
    }
  }

  return { busy, message, fields, run, reset }
}
