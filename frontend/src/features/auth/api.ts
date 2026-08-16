import { http } from '../../services/httpClient'
import type { AuthResponse } from '../../types/api'

export const authApi = {
  login: (email: string, password: string) => http.post<AuthResponse>('/auth/login', { email, password }),
  register: (email: string, password: string, name: string) =>
    http.post<AuthResponse>('/auth/register', { email, password, name }),
  me: () => http.get<{ id: string; email: string; name: string }>('/auth/me'),
  /** Answers the same way whether or not the address is registered, so the screen must
   *  not read anything into it beyond "we are done here". */
  forgotPassword: (email: string) => http.post<{ detail: string }>('/auth/forgot-password', { email }),
  /** Returns a session: whoever opened the link has just proved they own the mailbox. */
  resetPassword: (token: string, newPassword: string) =>
    http.post<AuthResponse>('/auth/reset-password', { token, new_password: newPassword }),
  changePassword: (currentPassword: string, newPassword: string) =>
    http.post<{ detail: string }>('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),
}
