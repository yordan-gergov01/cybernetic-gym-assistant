import { DEDICATION, GOALS } from '../constants'
import { OptionCard, StepLayout, TextField } from '../components'
import type { StepProps } from '../types'

/** Henselmans goal validation thresholds - the same ones the backend enforces. */
const CUT_ABOVE = { male: 15, female: 25 }
const BULK_BELOW = { male: 10, female: 18 }

function goalWarning(draft: StepProps['draft']): string | null {
  const { body_fat_pct: bf, sex, goal } = draft
  if (!bf || !sex || !goal) return null
  if (bf > CUT_ABOVE[sex] && (goal === 'bulk' || goal === 'maintain')) {
    return `При ${bf}% телесни мазнини качването на маса ще донесе предимно мазнини. Препоръчваме първо сваляне - по-добра инсулинова чувствителност и по-добра основа за покачване на мускулна маса после.`
  }
  if (bf < BULK_BELOW[sex] && (goal === 'cut' || goal === 'aggressive_cut')) {
    return `При ${bf}% телесни мазнини по-нататъшно сваляне рискува хормонални нарушения и загуба на мускул. Препоръчваме покачване.`
  }
  return null
}

export function GoalStep({ draft, update }: StepProps) {
  const warning = goalWarning(draft)
  return (
    <StepLayout title="Каква е целта ти?" explainer="Целта определя калорийния баланс и очакваната скорост на промяна.">
      {GOALS.map((goal) => (
        <OptionCard
          key={goal.value}
          option={goal}
          selected={draft.goal === goal.value}
          onSelect={() => update({ goal: goal.value as StepProps['draft']['goal'] })}
        />
      ))}

      {/* The backend will validate this too; showing it here means the user is not
          surprised by a different goal appearing in their plan. */}
      {warning && (
        <div className="rounded-2xl border border-warn-400/40 bg-warn-400/10 p-4">
          <p className="mb-1 font-semibold text-warn-400">Препоръчваме друга цел</p>
          <p className="text-sm leading-relaxed text-chalk-300">{warning}</p>
        </div>
      )}

      <TextField
        label="Разкажи повече (по избор)"
        placeholder="напр. подготвям се за сватба през май"
        value={draft.goal_details ?? undefined}
        onChange={(goal_details) => update({ goal_details })}
        rows={2}
      />
    </StepLayout>
  )
}

export function DedicationStep({ draft, update }: StepProps) {
  return (
    <StepLayout
      title="Колко агресивно да е темпото?"
      explainer="Определя колко голям дефицит или излишък ще заложим. Няма грешен отговор - по-бавното темпо е препоръчително, за по-лесен процес."
    >
      {DEDICATION.map((option) => (
        <OptionCard
          key={option.value}
          option={option}
          selected={draft.dedication_level === option.value}
          onSelect={() => update({ dedication_level: option.value as StepProps['draft']['dedication_level'] })}
        />
      ))}
    </StepLayout>
  )
}
