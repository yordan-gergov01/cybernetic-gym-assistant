// Single HTTP entry point for the backend.
// Attaches the JWT, turns error responses into real Error objects (so TanStack Query
// can surface them), and clears the session on 401 instead of failing silently.

const BASE = '/api/v1'
const TOKEN_KEY = 'cga_token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (token: string) => localStorage.setItem(TOKEN_KEY, token)
export const clearToken = () => localStorage.removeItem(TOKEN_KEY)

/** Listeners notified when the API rejects our token.
 *
 *  Dropping the token from storage is not enough: React still holds "signed in" in
 *  state, so the app keeps rendering screens that can no longer save anything. Without
 *  this signal a user can fill in a sixteen-step form against a dead session and only
 *  find out on the final submit. */
const sessionListeners = new Set<() => void>()

/** Endpoints where a 401 is a failed sign-in attempt, not a dead session. */
const SIGN_IN_PATHS = ['/auth/login', '/auth/register']

export function onSessionExpired(listener: () => void): () => void {
  sessionListeners.add(listener)
  return () => sessionListeners.delete(listener)
}

export class ApiError extends Error {
  status: number
  /** Field paths the backend rejected (422), so a form can mark the exact inputs. */
  fields: string[]

  constructor(status: number, message: string, fields: string[] = []) {
    super(message)
    this.status = status
    this.fields = fields
    this.name = 'ApiError'
  }
}

type RequestOptions = Omit<RequestInit, 'body'> & { body?: unknown }

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers, ...rest } = options
  const isForm = body instanceof FormData
  const token = getToken()

  const response = await fetch(`${BASE}${path}`, {
    ...rest,
    headers: {
      ...(isForm || body === undefined ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: isForm ? body : body !== undefined ? JSON.stringify(body) : undefined,
  })

  // A 401 means two completely different things depending on where it came from. On
  // the sign-in endpoints it is "wrong email or password" and the backend already says
  // so; anywhere else it is a token the API no longer accepts, which ends the session.
  // Treating both the same way told people signing in that their session had expired.
  if (response.status === 401 && !SIGN_IN_PATHS.some((p) => path.startsWith(p))) {
    clearToken()
    sessionListeners.forEach((listener) => listener())
    throw new ApiError(401, 'Сесията изтече. Влез отново.')
  }

  if (!response.ok) {
    // The API answers with `detail` as a ready Bulgarian sentence (app/core/errors.py),
    // plus `fields` on a validation failure. Anything else is not ours to show.
    let detail = 'Нещо се обърка. Опитай пак.'
    let fields: string[] = []
    try {
      const data = await response.json()
      if (typeof data.detail === 'string') detail = data.detail
      if (Array.isArray(data.fields)) fields = data.fields.map(String)
    } catch {
      /* non-JSON error body - keep the generic sentence */
    }
    throw new ApiError(response.status, detail, fields)
  }

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const http = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PATCH', body }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
