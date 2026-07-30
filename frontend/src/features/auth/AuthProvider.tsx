import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { clearToken, getToken, setToken } from '../../services/httpClient'
import type { AuthResponse } from '../../types/api'
import { authApi } from './api'
import { AuthContext } from './AuthContext'

const NAME_KEY = 'cga_name'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthed, setIsAuthed] = useState(() => !!getToken())
  const [name, setName] = useState<string | null>(() => localStorage.getItem(NAME_KEY))

  const persist = useCallback((res: AuthResponse) => {
    setToken(res.access_token)
    localStorage.setItem(NAME_KEY, res.name)
    setName(res.name)
    setIsAuthed(true)
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

  const logout = useCallback(() => {
    clearToken()
    localStorage.removeItem(NAME_KEY)
    setName(null)
    setIsAuthed(false)
  }, [])

  const value = useMemo(
    () => ({ isAuthed, name, login, register, logout }),
    [isAuthed, name, login, register, logout],
  )

  return <AuthContext value={value}>{children}</AuthContext>
}
