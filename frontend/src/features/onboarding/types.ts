import type { BFAssessment, PhotoAngle, ProfileCreate } from '../../types/api'

/** One photo slot in the body-fat step: the id survives a refresh, the presigned url
 *  is what the thumbnail shows. */
export type BfPhoto = { angle: PhotoAngle; id: string; url?: string | null }

/** The wizard builds a profile incrementally, so every field is optional while in
 *  progress and validated per step before the user can advance. */
export type ProfileDraft = Partial<ProfileCreate> & {
  lifts?: Record<string, { weight: number; reps: number }>
  equipment_details?: Record<string, boolean | string>
  /** Wizard-only: how the user chose to supply body fat. Stripped before submitting. */
  bf_method?: 'known' | 'photos' | 'unknown'
  /** Wizard-only: photos uploaded in the body-fat step and the estimate they produced.
   *  Kept in the draft so a refresh mid-setup does not lose an assessment that already
   *  cost a vision call. Stripped before submitting. */
  bf_photos?: BfPhoto[]
  bf_assessment?: BFAssessment
}

/** Draft keys the wizard uses for itself - the API never sees them. */
export const WIZARD_ONLY_KEYS = ['bf_method', 'bf_photos', 'bf_assessment'] as const

export type StepId =
  | 'welcome'
  | 'basics'
  | 'bodyfat'
  | 'goal'
  | 'dedication'
  | 'activity'
  | 'stress'
  | 'sleep'
  | 'experience'
  | 'schedule'
  | 'equipment'
  | 'increments'
  | 'strength'
  | 'focus'
  | 'limitations'
  | 'nutrition'

export type StepProps = {
  draft: ProfileDraft
  update: (patch: ProfileDraft) => void
}
