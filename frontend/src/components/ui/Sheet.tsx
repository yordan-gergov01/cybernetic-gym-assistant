import { useEffect, type ReactNode } from 'react'
import { Icon } from './Icon'

/** Bottom sheet: opens a detail without leaving the screen underneath.
 *
 *  Anchored to the bottom edge because it is opened one-handed — both the content and
 *  the way out have to sit inside the thumb arc. Escape closes it as well as the
 *  backdrop, so keyboard users are not trapped behind it.
 *
 *  The bottom inset is inlined instead of using `safe-bottom`: that utility sets
 *  padding-bottom outright and would fight the sheet's own padding. */
export function Sheet({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean
  onClose: () => void
  title?: string
  children: ReactNode
}) {
  useEffect(() => {
    if (!open) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      <button
        type="button"
        aria-label="Затвори"
        onClick={onClose}
        className="absolute inset-0 bg-black/70"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="anim-in relative w-full max-w-lg rounded-t-3xl border border-ink-700 bg-ink-900 px-4 pt-4"
        style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 16px)' }}
      >
        <div className="mx-auto mb-4 h-1.5 w-10 rounded-full bg-ink-600" />
        {title && (
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="section-title min-w-0 flex-1 truncate text-chalk-50">{title}</h3>
            <button
              type="button"
              onClick={onClose}
              aria-label="Затвори"
              className="tap -mr-2 grid h-11 w-11 shrink-0 place-items-center rounded-xl text-chalk-500 active:bg-ink-800"
            >
              <Icon name="close" size={20} />
            </button>
          </div>
        )}
        {children}
      </div>
    </div>
  )
}
