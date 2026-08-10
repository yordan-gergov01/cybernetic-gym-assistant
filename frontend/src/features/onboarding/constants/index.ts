/** Wizard option sets, grouped by the part of the intake they belong to.
 *
 * Wording and grouping follow the Henselmans PT client intake form - the descriptions
 * are the concrete examples the form uses ("office job with standard life chores"),
 * because a vague label makes people pick the wrong bucket and skews every downstream
 * calculation. */

export { STEP_GROUP } from './flow'
export { BF_PHOTO_ANGLES, CONFIDENCE_LABEL } from './body'
export { GOALS, DEDICATION } from './goal'
export { ACTIVITY, STRESS, SLEEP } from './lifestyle'
export {
  TRAINING_STATUS,
  EQUIPMENT,
  EQUIPMENT_CHECKLIST,
  STRENGTH_LIFTS,
  BARBELL_INCREMENTS,
  DUMBBELL_INCREMENTS,
  TRAINING_DAYS,
  SESSION_MINUTES,
} from './training'
export { MUSCLES, MAX_PRIORITY_MUSCLES, DIETARY } from './preferences'
