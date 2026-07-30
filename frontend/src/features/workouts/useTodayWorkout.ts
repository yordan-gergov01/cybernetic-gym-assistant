import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '../../constants/query-keys'
import type { ProgramDay, ProgramExercise, WorkoutSetInput } from '../../types/api'
import { todayIso } from '../../utils/date'
import { workoutsApi } from './api'

export type SetEntry = { weight: string; reps: string; rir: string; done: boolean }

/** All state for the in-gym screen: which day to train, and the sets logged so far. */
export function useTodayWorkout() {
  const queryClient = useQueryClient()
  const [entries, setEntries] = useState<Record<string, SetEntry[]>>({})

  const programs = useQuery({ queryKey: queryKeys.programs, queryFn: workoutsApi.listPrograms })
  const activeId = programs.data?.find((p) => p.status === 'active')?.id ?? programs.data?.[0]?.id

  const program = useQuery({
    queryKey: queryKeys.program(activeId),
    queryFn: () => workoutsApi.getProgram(activeId!),
    enabled: !!activeId,
  })

  // TODO: pick the day by calendar position using the program start date and the
  // completed-workout history. For now the first non-rest day of the earliest week.
  const day: ProgramDay | undefined = useMemo(() => {
    const weeks = [...(program.data?.weeks ?? [])].sort((a, b) => a.week_number - b.week_number)
    for (const week of weeks) {
      const match = [...week.days].sort((a, b) => a.day_number - b.day_number).find((d) => !d.is_rest_day)
      if (match) return match
    }
    return undefined
  }, [program.data])

  const logWorkout = useMutation({
    mutationFn: workoutsApi.logWorkout,
    onSuccess: () => {
      setEntries({})
      queryClient.invalidateQueries({ queryKey: queryKeys.program(activeId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.workouts })
    },
  })

  const rowsFor = (exercise: ProgramExercise): SetEntry[] =>
    entries[exercise.id] ??
    Array.from({ length: exercise.sets_prescribed ?? 3 }, () => ({
      // Pre-fill with the deterministic progression target so the user only confirms.
      weight: exercise.target_weight_kg ? String(exercise.target_weight_kg) : '',
      reps: exercise.target_reps ? String(exercise.target_reps) : '',
      rir: '',
      done: false,
    }))

  const updateRow = (exercise: ProgramExercise, index: number, patch: Partial<SetEntry>) => {
    setEntries((prev) => {
      const rows = prev[exercise.id] ?? rowsFor(exercise)
      return { ...prev, [exercise.id]: rows.map((row, i) => (i === index ? { ...row, ...patch } : row)) }
    })
  }

  const completedCount = Object.values(entries)
    .flat()
    .filter((row) => row.done).length

  const finish = () => {
    if (!day || !activeId) return
    const sets: WorkoutSetInput[] = []
    for (const exercise of day.exercises) {
      ;(entries[exercise.id] ?? []).forEach((row, index) => {
        if (!row.done) return
        sets.push({
          program_exercise_id: exercise.id,
          exercise_name: exercise.exercise_name,
          set_number: index + 1,
          weight_kg: row.weight ? Number(row.weight) : null,
          reps: row.reps ? Number(row.reps) : null,
          rir_actual: row.rir !== '' ? Number(row.rir) : null,
        })
      })
    }
    if (!sets.length) return
    logWorkout.mutate({ program_id: activeId, day_id: day.id, date: todayIso(), sets })
  }

  return {
    isLoading: programs.isLoading || program.isLoading,
    error: programs.error ?? program.error,
    refetch: () => programs.refetch(),
    hasProgram: !!activeId,
    programName: program.data?.name,
    day,
    rowsFor,
    updateRow,
    completedCount,
    finish,
    isSaving: logWorkout.isPending,
    saveError: logWorkout.error,
  }
}
