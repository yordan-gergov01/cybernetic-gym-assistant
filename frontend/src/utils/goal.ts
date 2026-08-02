import type { ProfileCreate } from '../types/api'

/** Goal validation against body fat, mirroring `validate_goal` in
 *  `backend/app/domain/calculators.py`. The backend decides what the plan actually uses;
 *  running the same rule here only means the user is warned before they commit to a goal
 *  instead of being surprised by a different one in their program.
 *
 *  Thresholds are the Henselmans ones: cut above 15% (men) / 25% (women), bulk below
 *  10% / 18%. */

const CUT_ABOVE = { male: 15, female: 25 }
const BULK_BELOW = { male: 10, female: 18 }

/** Which goal the methodology recommends instead, or null when the stated goal is fine. */
export function conflictingGoal(
  bodyFatPct: number | null | undefined,
  sex: ProfileCreate['sex'] | undefined,
  goal: ProfileCreate['goal'] | undefined,
): 'cut' | 'bulk' | null {
  if (!bodyFatPct || !sex || !goal) return null
  if (bodyFatPct > CUT_ABOVE[sex] && (goal === 'bulk' || goal === 'maintain')) return 'cut'
  if (bodyFatPct < BULK_BELOW[sex] && (goal === 'cut' || goal === 'aggressive_cut')) return 'bulk'
  return null
}
