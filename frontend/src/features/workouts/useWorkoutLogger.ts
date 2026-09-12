import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '../../constants/query-keys'
import type { ProgramExercise, TodayView, WorkoutSetInput } from '../../types/api'
import { todayIso } from '../../utils/date'
import { parseDecimal } from '../../utils/number'
import { workoutsApi } from './api'

export type SetEntry = { weight: string; reps: string; rir: string; done: boolean }

/** What to train today. The backend decides everything - which session is next, whether
 *  today is a rest day, the weekly volume - so this only fetches it. */
export function useToday() {
  return useQuery<TodayView>({ queryKey: queryKeys.today, queryFn: workoutsApi.today, retry: false })
}

/** The sets logged during one session.
 *
 *  Rows start pre-filled with the deterministic progression target, so a set is normally
 *  confirmed rather than typed - between sets, with one hand, typing is the enemy. */
export function useWorkoutLogger({
  programId,
  dayId,
  exercises,
}: {
  programId: string
  dayId: string
  exercises: ProgramExercise[]
}) {
  const queryClient = useQueryClient()
  const [entries, setEntries] = useState<Record<string, SetEntry[]>>({})

  const logWorkout = useMutation({
    // A whole session's sets are in this call; if saving fails the user has to see it
    // while the numbers are still on screen, not after a strip has faded.
    meta: { inlineError: true },
    mutationFn: workoutsApi.logWorkout,
    onSuccess: () => {
      setEntries({})
      // Today changes the moment a session is logged: the next session, the week strip
      // and the volume bars all move.
      queryClient.invalidateQueries({ queryKey: queryKeys.today })
      queryClient.invalidateQueries({ queryKey: queryKeys.workouts })
      queryClient.invalidateQueries({ queryKey: queryKeys.program(programId) })
    },
  })

  const rowsFor = (exercise: ProgramExercise): SetEntry[] =>
    entries[exercise.id] ??
    Array.from({ length: exercise.sets_prescribed ?? 3 }, () => ({
      weight: exercise.target_weight_kg ? String(exercise.target_weight_kg) : '',
      reps: exercise.target_reps ? String(exercise.target_reps) : '',
      rir: '',
      done: false,
    }))

  /** An extra set beyond the prescribed count. People do them, and a set performed but
   *  not logged is a hole in the volume the coaching decisions are made from. */
  const addRow = (exercise: ProgramExercise) => {
    setEntries((prev) => {
      const rows = prev[exercise.id] ?? rowsFor(exercise)
      const last = rows[rows.length - 1]
      return {
        ...prev,
        [exercise.id]: [...rows, { weight: last?.weight ?? '', reps: last?.reps ?? '', rir: '', done: false }],
      }
    })
  }

  const updateRow = (exercise: ProgramExercise, index: number, patch: Partial<SetEntry>) => {
    setEntries((prev) => {
      const rows = prev[exercise.id] ?? rowsFor(exercise)
      return { ...prev, [exercise.id]: rows.map((row, i) => (i === index ? { ...row, ...patch } : row)) }
    })
  }

  const completedCount = Object.values(entries)
    .flat()
    .filter((row) => row.done).length

  // Exercises nobody has touched yet still count towards the session: the bar has to
  // show how much of the whole workout is left, not how much of what has been opened.
  const plannedCount = exercises.reduce(
    (total, exercise) => total + (entries[exercise.id]?.length ?? exercise.sets_prescribed ?? 3),
    0,
  )

  const finish = () => {
    const sets: WorkoutSetInput[] = []
    for (const exercise of exercises) {
      ;(entries[exercise.id] ?? []).forEach((row, index) => {
        if (!row.done) return
        sets.push({
          program_exercise_id: exercise.id,
          exercise_name: exercise.exercise_name,
          set_number: index + 1,
          // parseDecimal, not Number: a comma from the phone keyboard would become NaN
          // and the logged weight would silently arrive as null.
          weight_kg: parseDecimal(row.weight) ?? null,
          reps: parseDecimal(row.reps) ?? null,
          rir_actual: parseDecimal(row.rir) ?? null,
        })
      })
    }
    if (!sets.length) return
    logWorkout.mutate({ program_id: programId, day_id: dayId, date: todayIso(), sets })
  }

  return {
    rowsFor,
    updateRow,
    addRow,
    completedCount,
    plannedCount,
    finish,
    isSaving: logWorkout.isPending,
    saveError: logWorkout.error,
  }
}
