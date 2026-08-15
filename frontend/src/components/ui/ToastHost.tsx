import { useSyncExternalStore } from 'react'
import { dismissToast, getToasts, subscribeToasts } from '../../services/toast'
import { Icon } from './Icon'

/** Where transient messages appear: above the bottom nav, in the thumb arc, so a toast
 *  can be dismissed with the same hand that is holding the phone.
 *
 *  `aria-live="polite"` rather than assertive: these report something that already
 *  happened, and interrupting a screen reader mid-sentence for that is rude. */
export function ToastHost() {
  const toasts = useSyncExternalStore(subscribeToasts, getToasts, getToasts)

  if (!toasts.length) return null

  return (
    <div
      aria-live="polite"
      className="pointer-events-none fixed inset-x-0 bottom-24 z-50 mx-auto flex max-w-lg flex-col gap-2 px-4"
    >
      {toasts.map((toast) => (
        <button
          key={toast.id}
          type="button"
          onClick={() => dismissToast(toast.id)}
          className={`anim-in pointer-events-auto flex w-full items-start gap-3 rounded-2xl border p-3.5 text-left backdrop-blur ${
            toast.tone === 'error'
              ? 'border-danger-400/40 bg-danger-400/15 text-danger-400'
              : 'border-ok-400/40 bg-ok-400/15 text-ok-400'
          }`}
        >
          <Icon name={toast.tone === 'error' ? 'alert' : 'check'} size={18} className="mt-0.5 shrink-0" />
          <span className="min-w-0 flex-1 text-sm leading-relaxed text-chalk-50">{toast.message}</span>
          <Icon name="close" size={16} className="mt-0.5 shrink-0 text-chalk-500" />
        </button>
      ))}
    </div>
  )
}
