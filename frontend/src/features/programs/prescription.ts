import { muscleLabel } from '../../constants/muscles'
import type { ProgramExercise } from '../../types/api'

/** How an exercise is prescribed, in the two densities the app needs.
 *
 *  Missing parts are dropped instead of rendered as "-": a program written without a
 *  RIR target should read as one, not as an incomplete row. */

/** "4 серии · 6–8 повт. · RIR 2" - for a full-width row that shows the muscle as a tag. */
export const prescriptionLong = (exercise: ProgramExercise): string =>
  [
    exercise.sets_prescribed ? `${exercise.sets_prescribed} серии` : null,
    exercise.reps_min && exercise.reps_max ? `${exercise.reps_min}–${exercise.reps_max} повт.` : null,
    exercise.rir_target !== null && exercise.rir_target !== undefined ? `RIR ${exercise.rir_target}` : null,
  ]
    .filter(Boolean)
    .join(' · ')

/** "4 × 6–8 · RIR 2 · Гърди" - for a sheet row, where there is no room for a tag. */
export const prescriptionCompact = (exercise: ProgramExercise): string =>
  [
    exercise.sets_prescribed && exercise.reps_min && exercise.reps_max
      ? `${exercise.sets_prescribed} × ${exercise.reps_min}–${exercise.reps_max}`
      : exercise.sets_prescribed
        ? `${exercise.sets_prescribed} серии`
        : null,
    exercise.rir_target !== null && exercise.rir_target !== undefined ? `RIR ${exercise.rir_target}` : null,
    muscleLabel(exercise.muscle_group) || null,
  ]
    .filter(Boolean)
    .join(' · ')
