import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Screen } from '../components/layout/Screen'
import { ErrorNote, Loading, Stat } from '../components/ui'
import { queryKeys } from '../constants/query-keys'
import { progressApi } from '../features/progress/api'
import { CoachingCard } from '../features/progress/CoachingCard'
import { TrendChart } from '../features/progress/TrendChart'
import { WeightForm } from '../features/progress/WeightForm'
import { todayIso } from '../utils/date'
import { formatRate, formatWeight } from '../utils/format'

export function ProgressPage() {
  const queryClient = useQueryClient()

  const trend = useQuery({ queryKey: queryKeys.weightTrend, queryFn: progressApi.trend })
  const coaching = useQuery({ queryKey: queryKeys.weightCoaching, queryFn: progressApi.coaching })

  const logWeight = useMutation({
    mutationFn: (kg: number) => progressApi.logWeight(todayIso(), kg),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.weightTrend })
      queryClient.invalidateQueries({ queryKey: queryKeys.weightCoaching })
    },
  })

  if (trend.isLoading) {
    return (
      <Screen title="Прогрес" subtitle="Тегло, тренд и корекции">
        <Loading />
      </Screen>
    )
  }
  if (trend.error) {
    return (
      <Screen title="Прогрес" subtitle="Тегло, тренд и корекции">
        <ErrorNote error={trend.error} onRetry={() => trend.refetch()} />
      </Screen>
    )
  }

  const data = trend.data!
  const rate = data.weekly_rate_kg ?? 0
  const arrow = data.direction === 'down' ? '↓' : data.direction === 'up' ? '↑' : '→'

  return (
    <Screen title="Прогрес" subtitle="Тегло, тренд и корекции">

      <WeightForm onSubmit={(kg) => logWeight.mutate(kg)} isPending={logWeight.isPending} />

      {logWeight.error && (
        <div className="mb-4">
          <ErrorNote error={logWeight.error} />
        </div>
      )}

      {data.status === 'insufficient_data' ? (
        <div className="card text-center text-sm text-chalk-500">
          Логни поне 3 измервания, за да се изчисли тренд.
        </div>
      ) : (
        <>
          <section className="card mb-4">
            <div className="mb-4 flex items-end justify-between gap-4">
              <Stat value={formatWeight(data.current_weight)} unit="кг" label="тренд (изгладено)" tone="accent" />
              <Stat
                value={`${arrow} ${formatRate(Math.abs(rate))}`}
                unit="кг/сед"
                label="скорост"
                tone={data.direction === 'stable' ? 'default' : 'ok'}
                size="sm"
              />
            </div>

            <TrendChart points={data.trend_points ?? []} />

            <p className="mt-2 text-center text-[11px] text-chalk-500">
              {data.total_entries} измервания · линията е изгладен тренд, точките са дневните стойности
            </p>
          </section>

          {coaching.data && <CoachingCard coaching={coaching.data} />}
        </>
      )}
    </Screen>
  )
}
