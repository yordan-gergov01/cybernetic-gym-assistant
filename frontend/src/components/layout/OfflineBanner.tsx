import { useSyncExternalStore } from 'react'

function subscribe(onChange: () => void): () => void {
  window.addEventListener('online', onChange)
  window.addEventListener('offline', onChange)
  return () => {
    window.removeEventListener('online', onChange)
    window.removeEventListener('offline', onChange)
  }
}

/** Whether the device thinks it has a connection.
 *
 *  `navigator.onLine` only knows about the network interface, not whether our API is
 *  reachable - a request can still fail while this says true. That case is covered by
 *  the error message on the request itself; this exists for the opposite one, where the
 *  phone is offline and nothing would explain why every action fails. */
function useOnline(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => navigator.onLine,
    () => true,
  )
}

/** Persistent strip, unlike a toast: being offline is a state, not an event, and it has
 *  to stay visible for as long as it lasts. */
export function OfflineBanner() {
  if (useOnline()) return null

  return (
    <div
      role="status"
      className="border-t border-warn-400/40 bg-warn-400/15 px-4 py-2 text-center text-xs font-medium text-warn-400"
    >
      Няма връзка с интернет. Вашите промени няма да се запазят, докато не сте обратно онлайн.
    </div>
  )
}
