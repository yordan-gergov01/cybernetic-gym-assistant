import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Screen } from '../components/layout/Screen'
import {
  Chip,
  ErrorNote,
  Icon,
  ListRow,
  Loading,
  SectionHeader,
} from '../components/ui'
import { queryKeys } from '../constants/query-keys'
import { photosApi } from '../features/photos/api'
import { progressApi } from '../features/progress/api'
import { BodyCompositionCard } from '../features/progress/BodyCompositionCard'
import { CoachingCard } from '../features/progress/CoachingCard'
import { StrengthList } from '../features/progress/StrengthList'
import { TrendChart } from '../features/progress/TrendChart'
import { WeightForm } from '../features/progress/WeightForm'
import { profileApi } from '../features/onboarding/api'
import { todayIso } from '../utils/date'
import { formatRateMagnitude, formatWeight } from '../utils/format'

/** Windows offered for the trend. The chart and the rate always describe the same
 *  period, because the window is applied on the backend before the trend is computed. */
const RANGES = [
  { label: '1 мес', days: 30 },
  { label: '3 мес', days: 90 },
  { label: '6 мес', days: 180 },
  { label: 'Всичко', days: 0 },
]

const STRENGTH_WEEKS = 4

export function ProgressPage() {
  const queryClient = useQueryClient()
  const [days, setDays] = useState(30)

  const trend = useQuery({
    queryKey: queryKeys.weightTrend(days),
    queryFn: () => progressApi.trend(days),
  })
  const coaching = useQuery({ queryKey: queryKeys.weightCoaching, queryFn: progressApi.coaching })
  const strength = useQuery({
    queryKey: queryKeys.strength(STRENGTH_WEEKS),
    queryFn: () => progressApi.strength(STRENGTH_WEEKS),
  })
  const photos = useQuery({ queryKey: queryKeys.photos, queryFn: photosApi.list })
  const profile = useQuery({ queryKey: queryKeys.profile, queryFn: profileApi.get })

  const logWeight = useMutation({
    mutationFn: (kg: number) => progressApi.logWeight(todayIso(), kg),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weight'] })
      queryClient.invalidateQueries({ queryKey: queryKeys.today })
    },
  })

  const data = trend.data
  const rate = data?.weekly_rate_kg ?? 0
  const arrow = data?.direction === 'down' ? '↓' : data?.direction === 'up' ? '↑' : '→'

  return (
    <Screen title="Прогрес" subtitle="Тренд, сила и състав">
      <section className="card">
        <p className="label-micro">Тегло днес (кг)</p>
        <div className="mt-2">
          <WeightForm onSubmit={(kg) => logWeight.mutate(kg)} isPending={logWeight.isPending} />
        </div>
        {logWeight.error && <ErrorNote error={logWeight.error} />}
      </section>

      <SectionHeader title="Тегло и тренд" />
      {trend.isLoading ? (
        <Loading />
      ) : trend.error ? (
        <ErrorNote error={trend.error} onRetry={() => trend.refetch()} />
      ) : data?.status === 'insufficient_data' ? (
        <p className="card text-sm text-chalk-500">
          Логни поне 3 измервания в този период, за да се изчисли тренд.
        </p>
      ) : (
        <section className="card">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="label-micro">Тренд тегло</p>
              <p className="stat mt-2">{formatWeight(data?.current_weight)}</p>
            </div>
            <div className="text-right">
              <p className="label-micro">Седмична скорост</p>
              <p
                className={`stat-sm mt-2 ${data?.direction === 'stable' ? 'text-chalk-50' : 'text-volt-400'}`}
              >
                {arrow} {formatRateMagnitude(rate)}
              </p>
              <p className="text-xs text-chalk-500">кг/сед</p>
            </div>
          </div>

          <div className="mt-4">
            <TrendChart points={data?.trend_points ?? []} />
          </div>

          <p className="mt-2 text-xs leading-relaxed text-chalk-500">
            Линията е изгладеният тренд, точките са дневните измервания
            {data?.total_entries ? ` · ${data.total_entries} измервания` : ''}.
          </p>

          <div className="mt-4 flex flex-wrap gap-2">
            {RANGES.map((range) => (
              <Chip
                key={range.days}
                label={range.label}
                selected={days === range.days}
                onToggle={() => setDays(range.days)}
              />
            ))}
          </div>
        </section>
      )}

      {coaching.data && (
        <>
          <SectionHeader title="Калорийна корекция" />
          <CoachingCard coaching={coaching.data} />
        </>
      )}

      <SectionHeader
        title="Снимки и състав"
        action={
          <Link to="/photos" className="flex items-center gap-1 text-sm font-semibold text-volt-400">
            Виж всички
            <Icon name="chevronRight" size={16} />
          </Link>
        }
      />
      <BodyCompositionCard
        bodyFatPct={profile.data?.body_fat_pct}
        method={profile.data?.bf_assessment_method}
        photos={photos.data ?? []}
      />

      <SectionHeader title="Прогресия на силата" />
      {strength.isLoading ? (
        <Loading />
      ) : strength.error ? (
        <ErrorNote error={strength.error} onRetry={() => strength.refetch()} />
      ) : (
        <StrengthList items={strength.data ?? []} weeks={STRENGTH_WEEKS} />
      )}

      <div className="mt-4">
        <ListRow
          to="/check-in"
          leading={<Icon name="target" size={18} />}
          title="Седмичен чек-ин"
          subtitle="Умора, сън, представяне → решение за deload."
          chevron
        />
      </div>
    </Screen>
  )
}
