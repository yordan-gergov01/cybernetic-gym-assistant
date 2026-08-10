import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { SubPageHeader } from '../components/layout/SubPageHeader'
import {
  ErrorNote,
  Icon,
  ListRow,
  Loading,
  SectionHeader,
  StatBox,
  Tag,
} from '../components/ui'
import { queryKeys } from '../constants/query-keys'
import { muscleLabel } from '../constants/muscles'
import { useAuth } from '../features/auth/useAuth'
import { profileApi } from '../features/onboarding/api'
import { programsApi } from '../features/programs/api'
import { formatKcal, formatGrams, formatWeight } from '../utils/format'

const LEVEL_LABELS: Record<number, string> = {
  1: 'Начинаещ',
  2: 'Средно напреднал',
  3: 'Напреднал',
}

const GOAL_LABELS: Record<string, string> = {
  bulk: 'Покачване на маса',
  cut: 'Сваляне на мазнини',
  aggressive_cut: 'Агресивно сваляне',
  maintain: 'Поддържане',
}

export function ProfilePage() {
  const { name, logout } = useAuth()
  const queryClient = useQueryClient()
  const profile = useQuery({ queryKey: queryKeys.profile, queryFn: profileApi.get })

  const recalculate = useMutation({
    mutationFn: programsApi.recalculate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.profile })
      queryClient.invalidateQueries({ queryKey: queryKeys.today })
    },
  })

  if (profile.isLoading) {
    return (
      <div className="min-h-dvh bg-ink-950">
        <SubPageHeader title="Профил" />
        <Loading />
      </div>
    )
  }

  if (profile.error || !profile.data) {
    return (
      <div className="min-h-dvh bg-ink-950">
        <SubPageHeader title="Профил" />
        <main className="mx-auto max-w-lg px-4 pt-4">
          <ErrorNote error={profile.error} onRetry={() => profile.refetch()} />
        </main>
      </div>
    )
  }

  const p = profile.data
  const energy = p.calculator_results?.energy ?? {}
  const goal = GOAL_LABELS[p.goal_validated || p.goal] ?? p.goal

  return (
    <div className="min-h-dvh bg-ink-950">
      <SubPageHeader title="Профил" />

      <main className="mx-auto max-w-lg px-4 pt-4 pb-12">
        <div className="flex items-center gap-3">
          <span className="grid h-14 w-14 place-items-center rounded-full bg-volt-500 font-display text-xl font-bold text-ink-950">
            {(name ?? '?').slice(0, 2)}
          </span>
          <div className="min-w-0">
            <p className="font-display text-xl font-bold">{name ?? 'Профил'}</p>
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              <Tag>{LEVEL_LABELS[p.training_status] ?? '—'}</Tag>
              <Tag>{goal}</Tag>
            </div>
          </div>
        </div>

        <SectionHeader title="Текущ план" />
        <section className="card">
          <div className="grid grid-cols-2 gap-3">
            <StatBox label="Калории" value={formatKcal(energy.target_kcal)} unit="ккал" />
            <StatBox label="TDEE" value={formatKcal(energy.tdee_kcal)} unit="ккал" />
            <StatBox label="Протеин" value={formatGrams(energy.protein_g)} unit="г" />
            <StatBox label="Въглехидрати" value={formatGrams(energy.carbs_g)} unit="г" />
            <StatBox label="Мазнини" value={formatGrams(energy.fat_g)} unit="г" />
            <StatBox label="Мазнини %" value={p.body_fat_pct ? `${p.body_fat_pct}%` : '—'} />
          </div>

          <button
            type="button"
            onClick={() => recalculate.mutate()}
            disabled={recalculate.isPending}
            className="btn-ghost mt-4 w-full"
          >
            {recalculate.isPending ? 'Преизчисляваме…' : 'Преизчисли'}
          </button>
          {recalculate.error && (
            <div className="mt-3">
              <ErrorNote error={recalculate.error} />
            </div>
          )}
        </section>

        <SectionHeader title="Данни" />
        <div className="space-y-2">
          <ListRow
            title="Основни данни"
            subtitle={`${p.age} г · ${formatWeight(p.height_cm)} см · ${formatWeight(p.bodyweight_kg)} кг`}
          />
          <ListRow
            title="Телесни мазнини"
            subtitle={
              p.body_fat_pct
                ? `${p.body_fat_pct}%${p.bf_assessment_method ? ` · ${p.bf_assessment_method}` : ''}`
                : 'Още няма оценка'
            }
          />
          <ListRow title="Цел" subtitle={goal} />
          <ListRow title="График" subtitle={`${p.training_days_per_week} дни седмично`} />
          <ListRow
            title="Приоритети"
            subtitle={
              p.priority_muscles?.length
                ? p.priority_muscles.map(muscleLabel).join(', ')
                : 'Няма избрани'
            }
          />
        </div>

        <SectionHeader title="Настройки" />
        <section className="card space-y-3 text-sm">
          <div className="flex items-center justify-between gap-3">
            <span className="text-chalk-300">Мерни единици</span>
            <span className="text-chalk-500">кг / см</span>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-chalk-300">Език</span>
            <span className="text-chalk-500">Български</span>
          </div>
          <p className="flex items-center gap-2 text-xs text-chalk-500">
            <Icon name="info" size={14} />
            Инсталирай приложението от менюто на браузъра си.
          </p>
        </section>

        <button type="button" onClick={logout} className="btn-ghost mt-6 w-full">
          Изход
        </button>
      </main>
    </div>
  )
}
