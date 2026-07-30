import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Screen } from '../components/layout/Screen'
import { ErrorNote, Loading } from '../components/ui'
import { queryKeys } from '../constants/query-keys'
import { nutritionApi } from '../features/nutrition/api'
import { FoodEntryList } from '../features/nutrition/FoodEntryList'
import { MacroSummary } from '../features/nutrition/MacroSummary'
import { QuickAddForm } from '../features/nutrition/QuickAddForm'
import { formatDayLabel, todayIso } from '../utils/date'

export function NutritionPage() {
  const queryClient = useQueryClient()
  const date = todayIso()
  const invalidate = () => queryClient.invalidateQueries({ queryKey: queryKeys.nutrition(date) })

  const daily = useQuery({ queryKey: queryKeys.nutrition(date), queryFn: () => nutritionApi.daily(date) })
  const logFood = useMutation({
    mutationFn: (text: string) => nutritionApi.logFood(date, text),
    onSuccess: invalidate,
  })
  const deleteEntry = useMutation({ mutationFn: nutritionApi.deleteEntry, onSuccess: invalidate })

  if (daily.isLoading) {
    return (
      <Screen title="Храна" subtitle={formatDayLabel(date)}>
        <Loading />
      </Screen>
    )
  }
  if (daily.error) {
    return (
      <Screen title="Храна" subtitle={formatDayLabel(date)}>
        <ErrorNote error={daily.error} onRetry={() => daily.refetch()} />
      </Screen>
    )
  }

  return (
    <Screen title="Храна" subtitle={formatDayLabel(date)}>

      <MacroSummary daily={daily.data!} />
      <QuickAddForm onSubmit={(text) => logFood.mutate(text)} isPending={logFood.isPending} />

      {logFood.error && (
        <div className="mb-4">
          <ErrorNote error={logFood.error} />
        </div>
      )}

      <FoodEntryList entries={daily.data!.entries} onDelete={(id) => deleteEntry.mutate(id)} />
    </Screen>
  )
}
