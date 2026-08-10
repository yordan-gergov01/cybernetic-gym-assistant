import type { StepId } from '../types'

/** Which part of the intake each step belongs to.
 *
 *  Sixteen questions in a row feel endless when the only thing on screen is "step 7 of
 *  16". Naming the section tells the user what is being asked about right now, and that
 *  the end is a section away rather than nine screens away. */
export const STEP_GROUP: Record<StepId, string> = {
  welcome: 'Начало',
  basics: 'Ти',
  bodyfat: 'Ти',
  goal: 'Цел',
  dedication: 'Цел',
  activity: 'Начин на живот',
  stress: 'Начин на живот',
  sleep: 'Начин на живот',
  experience: 'Тренировки',
  schedule: 'Тренировки',
  equipment: 'Тренировки',
  increments: 'Тренировки',
  strength: 'Тренировки',
  focus: 'Приоритети',
  limitations: 'Приоритети',
  nutrition: 'Хранене',
}
