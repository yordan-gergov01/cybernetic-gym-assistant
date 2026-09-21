// Single HTTP entry point for the backend.
// Attaches the JWT, turns error responses into real Error objects (so TanStack Query
// can surface them), and clears the session on 401 instead of failing silently.

import { STORAGE_KEYS } from '../constants/storage'

const BASE = '/api/v1'
const TOKEN_KEY = STORAGE_KEYS.token

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

type RequestOptions = Omit<RequestInit, 'body'> & { body?: unknown; timeoutMs?: number }

/** A request that hangs is worse than one that fails: in the gym the user is left
 *  staring at a spinner between sets with no way to tell whether it is still coming. */
export const DEFAULT_TIMEOUT_MS = 15_000

/** For the endpoints that wait on a model - program generation, the body-fat read, food
 *  estimation, the coach. Thirty seconds of thinking is normal there, not a fault. */
export const MODEL_TIMEOUT_MS = 120_000

/** No response at all: the backend cannot describe this one, so the sentence is written
 *  here. Status 0 marks it as "never reached the API" for callers that care. */
function unreachable(error: unknown): ApiError {
  if (error instanceof DOMException && error.name === 'AbortError') {
    return new ApiError(0, 'Заявката отне твърде дълго. Провери връзката и опитай пак.')
  }
  return new ApiError(0, 'Няма връзка със сървъра. Провери интернета и опитай пак.')
}

/** Throw if the API refused the request, in the one shape every screen knows how to show. */
async function rejectFailures(response: Response, path: string): Promise<void> {
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
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers, timeoutMs = DEFAULT_TIMEOUT_MS, signal, ...rest } = options
  const isForm = body instanceof FormData
  const token = getToken()

  const timeout = new AbortController()
  const timer = setTimeout(() => timeout.abort(), timeoutMs)

  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, {
      ...rest,
      signal: signal ?? timeout.signal,
      headers: {
        ...(isForm || body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
      body: isForm ? body : body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch (error) {
    throw unreachable(error)
  } finally {
    clearTimeout(timer)
  }

  await rejectFailures(response, path)

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

/** One Server-Sent Event: the name the server tagged it with, and its raw `data` text. */
export type SseEvent = { event: string; data: string }

/** POST and read the reply as it is written, instead of waiting for all of it.
 *
 *  `EventSource` cannot do this - it is GET-only and cannot carry the Authorization
 *  header - so the stream is read off `fetch` by hand. The timeout covers the whole
 *  answer rather than only the headers: on a streamed reply the headers arrive at once,
 *  so a timeout that stopped there would guard nothing. */
export async function* streamEvents(
  path: string,
  body: unknown,
  { timeoutMs = MODEL_TIMEOUT_MS }: Options = {},
): AsyncGenerator<SseEvent> {
  const token = getToken()
  const timeout = new AbortController()
  const timer = setTimeout(() => timeout.abort(), timeoutMs)

  try {
    let response: Response
    try {
      response = await fetch(`${BASE}${path}`, {
        method: 'POST',
        signal: timeout.signal,
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
      })
    } catch (error) {
      throw unreachable(error)
    }

    await rejectFailures(response, path)
    if (!response.body) throw new ApiError(0, 'Отговорът не пристигна. Опитай пак.')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    for (;;) {
      let chunk: ReadableStreamReadResult<Uint8Array>
      try {
        chunk = await reader.read()
      } catch (error) {
        throw unreachable(error)
      }
      if (chunk.done) break
      // A UTF-8 character can be split across two chunks, and Bulgarian spends two bytes
      // a letter - decoding each chunk on its own would cut letters in half.
      buffer += decoder.decode(chunk.value, { stream: true })
      for (;;) {
        const end = buffer.indexOf(EVENT_SEPARATOR)
        if (end === -1) break
        const event = parseEvent(buffer.slice(0, end))
        buffer = buffer.slice(end + EVENT_SEPARATOR.length)
        if (event) yield event
      }
    }
  } finally {
    clearTimeout(timer)
  }
}

/** SSE ends an event with a blank line. */
const EVENT_SEPARATOR = '\n\n'

/** One `event:`/`data:` block, or null for a block that names no event - a keep-alive
 *  comment, or the empty tail after the last separator. */
function parseEvent(block: string): SseEvent | null {
  let event = ''
  const data: string[] = []
  for (const line of block.replace(/\r/g, '').split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) data.push(line.slice(5).replace(/^ /, ''))
  }
  return event ? { event, data: data.join('\n') } : null
}

type Options = { timeoutMs?: number }

export const http = {
  get: <T>(path: string, options?: Options) => request<T>(path, options),
  post: <T>(path: string, body?: unknown, options?: Options) =>
    request<T>(path, { ...options, method: 'POST', body }),
  put: <T>(path: string, body?: unknown, options?: Options) =>
    request<T>(path, { ...options, method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown, options?: Options) =>
    request<T>(path, { ...options, method: 'PATCH', body }),
  delete: <T>(path: string, options?: Options) => request<T>(path, { ...options, method: 'DELETE' }),
}
