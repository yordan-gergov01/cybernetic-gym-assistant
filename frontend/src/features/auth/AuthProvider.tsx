import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { clearToken, getToken, onSessionExpired, setToken } from '../../services/httpClient'
import type { AuthResponse } from '../../types/api'
import { STORAGE_KEYS } from '../../constants/storage'
import { authApi } from './api'
import { AuthContext } from './AuthContext'

const NAME_KEY = STORAGE_KEYS.name


export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthed, setIsAuthed] = useState(() => !!getToken())
  const [sessionExpired, setSessionExpired] = useState(false)
  const [name, setName] = useState<string | null>(() => localStorage.getItem(NAME_KEY))

  // The token can be rejected by any request, not just a deliberate logout. Reacting
  // here means the user lands on the login screen the moment the session dies, instead
  // of carrying on in a UI that can no longer save anything.
  useEffect(
    () =>
      onSessionExpired(() => {
        setIsAuthed(false)
        setSessionExpired(true)
      }),
    [],
  )

  const persist = useCallback((res: AuthResponse) => {
    setToken(res.access_token)
    localStorage.setItem(NAME_KEY, res.name)
    setName(res.name)
    setIsAuthed(true)
    setSessionExpired(false)
  }, [])

  const login = useCallback(
    async (email: string, password: string) => persist(await authApi.login(email, password)),
    [persist],
  )

  const register = useCallback(
    async (email: string, password: string, userName: string) =>
      persist(await authApi.register(email, password, userName)),
    [persist],
  )

  const resetPassword = useCallback(
    async (token: string, newPassword: string) =>
      persist(await authApi.resetPassword(token, newPassword)),
    [persist],
  )

  // The onboarding draft is deliberately left alone: it is the user's unsaved work, and
  // signing out - or being signed out - must not throw it away.
  const logout = useCallback(() => {
    clearToken()
    localStorage.removeItem(NAME_KEY)
    setName(null)
    setIsAuthed(false)
    setSessionExpired(false)
  }, [])

  const value = useMemo(
    () => ({ isAuthed, sessionExpired, name, login, register, resetPassword, logout }),
    [isAuthed, sessionExpired, name, login, register, resetPassword, logout],
  )

  return <AuthContext value={value}>{children}</AuthContext>
}
