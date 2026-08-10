import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { SubPageHeader } from '../components/layout/SubPageHeader'
import { EmptyState, ErrorNote, Icon, ListRow, Loading, type IconName } from '../components/ui'
import { notificationsApi } from '../features/notifications/api'
import { formatRelativeTime } from '../utils/date'

const NOTIFICATION_ICONS: Record<string, IconName> = {
  weight: 'scale',
  workout: 'dumbbell',
  nutrition: 'utensils',
  fatigue: 'alert',
  program: 'calendar',
}

export function NotificationsPage() {
  const queryClient = useQueryClient()
  const list = useQuery({ queryKey: ['notifications'], queryFn: notificationsApi.list })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['notifications'] })
  const markRead = useMutation({ mutationFn: notificationsApi.markRead, onSuccess: invalidate })
  const markAll = useMutation({ mutationFn: notificationsApi.markAllRead, onSuccess: invalidate })

  const items = list.data ?? []
  const unread = items.filter((n) => !n.is_read).length

  return (
    <div className="min-h-dvh bg-ink-950">
      <SubPageHeader
        title="Известия"
        action={
          unread > 0 ? (
            <button
              type="button"
              onClick={() => markAll.mutate()}
              disabled={markAll.isPending}
              className="tap shrink-0 px-1 text-sm font-semibold text-volt-400 disabled:opacity-40"
            >
              Отбележи всички
            </button>
          ) : undefined
        }
      />

      <main className="mx-auto max-w-lg px-4 pt-4 pb-10">
        {list.isLoading ? (
          <Loading />
        ) : list.error ? (
          <ErrorNote error={list.error} onRetry={() => list.refetch()} />
        ) : !items.length ? (
          <EmptyState title="Няма известия" hint="Ще ти пишем, когато има какво да се направи." />
        ) : (
          <div className="space-y-2">
            {items.map((item) => (
              <ListRow
                key={item.id}
                accent={!item.is_read}
                onClick={item.is_read ? undefined : () => markRead.mutate(item.id)}
                leading={<Icon name={NOTIFICATION_ICONS[item.type] ?? 'bell'} size={18} />}
                title={item.title || 'Известие'}
                subtitle={
                  <>
                    {item.body}
                    <span className="mt-1 block text-xs text-chalk-500">
                      {formatRelativeTime(item.created_at)}
                    </span>
                  </>
                }
              />
            ))}
          </div>
        )}

        {markAll.error && (
          <div className="mt-4">
            <ErrorNote error={markAll.error} />
          </div>
        )}
      </main>
    </div>
  )
}
