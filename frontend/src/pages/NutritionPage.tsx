import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Screen } from '../components/layout/Screen'
import { EmptyState, ErrorNote, Icon, SectionHeader, SkeletonList } from '../components/ui'
import { mealForHour } from '../constants/nutrition'
import { NUTRITION_VISIBLE_DAYS } from '../constants/history'
import { HEADER_ACTIONS } from '../constants/navigation'
import { queryKeys } from '../constants/query-keys'
import { nutritionApi } from '../features/nutrition/api'
import { DateStrip } from '../features/nutrition/DateStrip'
import { FoodEntryList } from '../features/nutrition/FoodEntryList'
import { MacroSummary } from '../features/nutrition/MacroSummary'
import { QuickAddForm } from '../features/nutrition/QuickAddForm'
import { recentDays, todayIso } from '../utils/date'



export function NutritionPage() {
  const queryClient = useQueryClient()
  const days = recentDays(NUTRITION_VISIBLE_DAYS)
  const [date, setDate] = useState(todayIso())

  const invalidate = () => queryClient.invalidateQueries({ queryKey: queryKeys.nutrition(date) })

  const daily = useQuery({
    queryKey: queryKeys.nutrition(date),
    queryFn: () => nutritionApi.daily(date),
  })

  const logFood = useMutation({
    // The meal is taken from the clock: people log as they eat, and the grouping is
    // only a heading - nothing downstream depends on it.
    mutationFn: (text: string) => nutritionApi.logFood(date, text, mealForHour(new Date().getHours())),
    onSuccess: invalidate,
  })

  const deleteEntry = useMutation({ mutationFn: nutritionApi.deleteEntry, onSuccess: invalidate })

  const strip = (
    <div className="mb-5">
      <DateStrip dates={days} selected={date} onSelect={setDate} />
    </div>
  )

  if (daily.isLoading) {
    return (
      <Screen title="Храна" actions={HEADER_ACTIONS.secondary}>
        {strip}
        <SkeletonList rows={3} />
      </Screen>
    )
  }

  if (daily.error || !daily.data) {
    return (
      <Screen title="Храна" actions={HEADER_ACTIONS.secondary}>
        {strip}
        <ErrorNote error={daily.error} onRetry={() => daily.refetch()} />
      </Screen>
    )
  }

  const entries = daily.data.entries

  return (
    <Screen title="Храна" subtitle="Целите идват от профила ти" actions={HEADER_ACTIONS.secondary}>
      {strip}

      <MacroSummary daily={daily.data} />

      <SectionHeader title="Бързо добавяне" />
      <QuickAddForm onSubmit={(text) => logFood.mutate(text)} isPending={logFood.isPending} />

      <SectionHeader title="Днешните хранения" />
      {entries.length === 0 ? (
        <EmptyState
          title="Още нищо за днес."
          hint="Опиши какво си ял с думи - разчитаме количествата и калориите."
          action={<Icon name="utensils" size={28} />}
        />
      ) : (
        <FoodEntryList
          entries={entries}
          onDelete={(id) => deleteEntry.mutate(id)}
          deletingId={deleteEntry.isPending ? deleteEntry.variables : undefined}
        />
      )}
    </Screen>
  )
}
