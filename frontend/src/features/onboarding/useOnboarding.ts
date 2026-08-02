import { useCallback, useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { profileApi } from './api'
import { WIZARD_ONLY_KEYS } from './types'
import type { ProfileDraft, StepId } from './types'
import type { ProfileCreate } from '../../types/api'

/** Step order. Grouped so related questions sit together and the wizard reads as a
 *  conversation rather than a form dump. */
export const STEPS: StepId[] = [
  'welcome',
  'basics',
  'bodyfat',
  'goal',
  'dedication',
  'activity',
  'stress',
  'sleep',
  'experience',
  'schedule',
  'equipment',
  'increments',
  'strength',
  'focus',
  'limitations',
  'nutrition',
]

const DRAFT_KEY = 'cga_onboarding_draft'

/** Every step must be answered - an incomplete profile produces a bad program, which
 *  is worse than a longer setup. `strength` is the one exception: a true beginner has
 *  no maxes to report yet. */
function isStepComplete(step: StepId, d: ProfileDraft): boolean {
  switch (step) {
    case 'welcome':
      return true
    case 'basics':
      return !!(d.age && d.sex && d.height_cm && d.bodyweight_kg)
    case 'bodyfat':
      // Photos must produce an accepted estimate here and now. Advancing on a
      // placeholder would mean calculating macros twice - once wrong.
      return d.body_fat_pct !== undefined || d.bf_method === 'unknown'
    case 'goal':
      return !!d.goal
    case 'dedication':
      return !!d.dedication_level
    case 'activity':
      return !!d.activity_level
    case 'stress':
      return !!d.stress_level && !!d.occupation
    case 'sleep':
      return !!d.sleep_quality && d.sleep_hours !== undefined
    case 'experience':
      return !!d.training_status && d.training_years !== undefined
    case 'schedule':
      return !!(d.training_days_per_week && d.session_duration_min)
    case 'equipment':
      return !!d.available_equipment
    case 'increments':
      return d.min_barbell_increment_kg !== undefined && d.min_dumbbell_increment_kg !== undefined
    case 'strength':
      return true
    case 'focus':
      return !!d.priority_muscles?.length
    case 'limitations':
      return true
    case 'nutrition':
      return !!d.dietary_restrictions
    default:
      return true
  }
}

export function useOnboarding(onDone: () => void) {
  const [index, setIndex] = useState(0)
  const [draft, setDraft] = useState<ProfileDraft>(() => {
    // Survive an accidental refresh mid-setup - 16 steps is a lot to redo.
    try {
      return JSON.parse(localStorage.getItem(DRAFT_KEY) ?? '{}')
    } catch {
      return {}
    }
  })

  const update = useCallback((patch: ProfileDraft) => {
    setDraft((prev) => {
      const next = { ...prev, ...patch }
      localStorage.setItem(DRAFT_KEY, JSON.stringify(next))
      return next
    })
  }, [])

  const save = useMutation({
    mutationFn: (payload: ProfileCreate) => profileApi.update(payload),
    onSuccess: () => {
      localStorage.removeItem(DRAFT_KEY)
      onDone()
    },
  })

  const step = STEPS[index]
  const canAdvance = useMemo(() => isStepComplete(step, draft), [step, draft])
  const isLast = index === STEPS.length - 1

  const next = () => {
    if (!canAdvance) return
    if (!isLast) {
      setIndex((i) => i + 1)
      return
    }
    const payload = { ...draft }
    for (const key of WIZARD_ONLY_KEYS) delete payload[key]
    save.mutate(payload as ProfileCreate)
  }

  const back = () => setIndex((i) => Math.max(0, i - 1))

  return {
    step,
    index,
    total: STEPS.length,
    draft,
    update,
    next,
    back,
    canAdvance,
    isLast,
    isSaving: save.isPending,
    saveError: save.error,
  }
}
