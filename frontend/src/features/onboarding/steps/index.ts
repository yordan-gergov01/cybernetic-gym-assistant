import type { ComponentType } from 'react'
import type { StepId, StepProps } from '../types'
import { BasicsStep, BodyFatStep, WelcomeStep } from './BodySteps'
import { DedicationStep, GoalStep } from './GoalSteps'
import { ActivityStep, SleepStep, StressStep } from './LifestyleSteps'
import { FocusStep, LimitationsStep, NutritionStep } from './PreferenceSteps'
import {
  EquipmentStep,
  ExperienceStep,
  IncrementsStep,
  ScheduleStep,
  StrengthStep,
} from './TrainingSteps'

/** Step id → component. The wizard renders whatever this maps to, so reordering the
 *  flow only means reordering STEPS in useOnboarding. */
export const STEP_COMPONENTS: Record<StepId, ComponentType<StepProps>> = {
  welcome: WelcomeStep,
  basics: BasicsStep,
  bodyfat: BodyFatStep,
  goal: GoalStep,
  dedication: DedicationStep,
  activity: ActivityStep,
  stress: StressStep,
  sleep: SleepStep,
  experience: ExperienceStep,
  schedule: ScheduleStep,
  equipment: EquipmentStep,
  increments: IncrementsStep,
  strength: StrengthStep,
  focus: FocusStep,
  limitations: LimitationsStep,
  nutrition: NutritionStep,
}
