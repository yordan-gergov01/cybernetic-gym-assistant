import type { ReactNode } from 'react'

export function Loading({ label = 'Зареждане…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-sm text-chalk-500">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-ink-600 border-t-volt-500" />
      {label}
    </div>
  )
}

/** Errors are always shown, never swallowed - the user must know when something failed. */
export function ErrorNote({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : 'Нещо се обърка.'
  return (
    <div className="rounded-2xl border border-danger-400/40 bg-danger-400/10 p-4">
      <p className="text-sm text-danger-400">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-ghost mt-3 w-full">
          Опитай пак
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, hint, action }: { title: string; hint?: string; action?: ReactNode }) {
  return (
    <div className="card flex flex-col items-center gap-2 py-12 text-center">
      <p className="font-semibold text-chalk-50">{title}</p>
      {hint && <p className="max-w-xs text-sm text-chalk-500">{hint}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}
