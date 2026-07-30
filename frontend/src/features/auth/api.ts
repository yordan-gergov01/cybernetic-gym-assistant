import { http } from '../../services/httpClient'
import type { AuthResponse } from '../../types/api'

export const authApi = {
  login: (email: string, password: string) => http.post<AuthResponse>('/auth/login', { email, password }),
  register: (email: string, password: string, name: string) =>
    http.post<AuthResponse>('/auth/register', { email, password, name }),
  me: () => http.get<{ id: string; email: string; name: string }>('/auth/me'),
}
