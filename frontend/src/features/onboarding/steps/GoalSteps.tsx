import { OptionCard, TextField } from '../../../components/ui'
import { DEDICATION, GOALS } from '../constants'
import { StepLayout } from '../components'
import { conflictingGoal } from '../../../utils/goal'
import type { StepProps } from '../types'

const WARNING: Record<'cut' | 'bulk', (bf: number) => string> = {
  cut: (bf) =>
    `При ${bf}% телесни мазнини качването на маса ще донесе предимно мазнини. Препоръчваме първо сваляне - по-добра инсулинова чувствителност и по-добра основа за покачване на мускулна маса после.`,
  bulk: (bf) =>
    `При ${bf}% телесни мазнини по-нататъшно сваляне рискува хормонални нарушения и загуба на мускул. Препоръчваме покачване.`,
}

export function GoalStep({ draft, update }: StepProps) {
  const recommended = conflictingGoal(draft.body_fat_pct, draft.sex, draft.goal)
  const warning = recommended && draft.body_fat_pct ? WARNING[recommended](draft.body_fat_pct) : null
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
