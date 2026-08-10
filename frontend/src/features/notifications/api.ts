import { http } from '../../services/httpClient'
import type { Notification } from '../../types/api'

export const notificationsApi = {
  list: () => http.get<Notification[]>('/notifications'),
  markRead: (id: string) => http.patch(`/notifications/${id}/read`),
  markAllRead: () => http.patch('/notifications/read-all'),
}
