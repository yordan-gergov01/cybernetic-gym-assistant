// Transient messages, held outside React on purpose.
//
// The failure that needs a toast most often comes from a mutation, and the query client
// that sees it is created before any provider exists. A plain store can be written to
// from there, from a service, or from a component, without threading a context through
// code that has nothing to do with the UI.

export type ToastTone = 'error' | 'ok'
export type Toast = { id: number; message: string; tone: ToastTone }

/** Long enough to read a sentence, short enough not to sit over the screen mid-set. */
const VISIBLE_MS = 5000

let toasts: Toast[] = []
let nextId = 1
const listeners = new Set<(toasts: Toast[]) => void>()

function emit() {
  // A new array each time: useSyncExternalStore compares by identity.
  toasts = [...toasts]
  listeners.forEach((listener) => listener(toasts))
}

export function subscribeToasts(listener: (toasts: Toast[]) => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function getToasts(): Toast[] {
  return toasts
}

export function dismissToast(id: number): void {
  toasts = toasts.filter((toast) => toast.id !== id)
  emit()
}

export function showToast(message: string, tone: ToastTone = 'error'): void {
  // The same failure repeated (a retry that fails again) stacks up into a wall of
  // identical strips; refreshing the one already on screen says the same thing.
  const existing = toasts.find((toast) => toast.message === message && toast.tone === tone)
  if (existing) {
    dismissToast(existing.id)
  }

  const id = nextId++
  toasts = [...toasts, { id, message, tone }]
  emit()
  setTimeout(() => dismissToast(id), VISIBLE_MS)
}
