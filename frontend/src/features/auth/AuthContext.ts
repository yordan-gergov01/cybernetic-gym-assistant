import { createContext } from 'react'

export type AuthState = {
  isAuthed: boolean
  /** True when the API rejected our token, so the login screen can say why. */
  sessionExpired: boolean
  name: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => void
}

/** Context object lives in its own module so the provider file only exports components
 *  and stays compatible with React Fast Refresh. */
export const AuthContext = createContext<AuthState | null>(null)
