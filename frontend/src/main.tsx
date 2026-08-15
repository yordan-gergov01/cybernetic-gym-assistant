import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { MutationCache, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import { AuthProvider } from './features/auth/AuthProvider'
import { ApiError } from './services/httpClient'
import { showToast } from './services/toast'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Phone use means flaky connections and frequent app switching: refetch when the
      // user comes back, but don't re-hit the API while they are mid-set.
      staleTime: 30_000,
      refetchOnWindowFocus: true,
      retry: 1,
    },
  },
  // A failed mutation is something the user just asked for, so it can never fail
  // silently. The toast is the channel for it, with one exception, marked
  // `meta.inlineError`: when losing the message would lose work - a long form, a logged
  // session, a generated program, or anything inside a sheet that covers the toast - the
  // failure stays on the screen that caused it, and the toast steps aside so the same
  // sentence is not shown twice.
  //
  // Failed *queries* are not toasted at all: a screen with no data renders ErrorNote
  // with a retry, which is the more useful answer than a strip that disappears.
  mutationCache: new MutationCache({
    onError: (error, _variables, _context, mutation) => {
      if (mutation.meta?.inlineError) return
      // The session-expired path already moves the user to the sign-in screen; a toast
      // on top of that only repeats what the screen is about to say.
      if (error instanceof ApiError && error.status === 401) return
      showToast(error instanceof Error ? error.message : 'Нещо се обърка. Опитай пак.')
    },
  }),
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
)
