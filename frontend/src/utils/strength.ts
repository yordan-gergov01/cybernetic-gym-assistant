/** Strength maths shown while the user is still typing.
 *
 *  These mirror `backend/app/domain/calculators.py` exactly. The backend stays the
 *  source of truth - this is a preview so the number feels earned, not a second
 *  implementation of the rule. If the two ever disagree, the backend wins and this
 *  file is the one to fix. */

/** Epley 1RM, same as `calculate_1rm(..., formula='epley')`. */
export const estimate1RM = (weightKg: number, reps: number): number => {
  const oneRm = reps === 1 ? weightKg : weightKg * (1 + reps / 30)
  return Math.round(oneRm * 10) / 10
}
