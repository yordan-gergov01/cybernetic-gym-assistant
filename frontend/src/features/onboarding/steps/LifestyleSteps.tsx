import { ACTIVITY, SLEEP, STRESS } from '../constants'
import { Field, NumberField, OptionCard, StepLayout } from '../components'
import type { StepProps } from '../types'

export function ActivityStep({ draft, update }: StepProps) {
  return (
    <StepLayout
      title="Колко активен си извън залата?"
      explainer="Ежедневната активност е голяма част от дневния ти разход - по-голяма от самите тренировки."
    >
      {ACTIVITY.map((option) => (
        <OptionCard
          key={option.value}
          option={option}
          selected={draft.activity_level === option.value}
          onSelect={() => update({ activity_level: option.value as StepProps['draft']['activity_level'] })}
        />
      ))}
    </StepLayout>
  )
}

export function StressStep({ draft, update }: StepProps) {
  return (
    <StepLayout
      title="Работа и стрес"
      explainer="Стресът намалява възстановяването и обема от тренировките, който можеш да понесеш. Професията подсказва и ритъма на деня ти."
    >
      <Field label="С какво се занимаваш?" hint="Общо е достатъчно: офис, строител, медик, IT.">
        <input
          className="input"
          placeholder="напр. софтуерен инженер"
          value={draft.occupation ?? ''}
          onChange={(e) => update({ occupation: e.target.value })}
        />
      </Field>

      <p className="label mt-4">Ниво на стрес</p>
      {STRESS.map((option) => (
        <OptionCard
          key={option.value}
          option={option}
          selected={draft.stress_level === option.value}
          onSelect={() => update({ stress_level: option.value as StepProps['draft']['stress_level'] })}
        />
      ))}
    </StepLayout>
  )
}

export function SleepStep({ draft, update }: StepProps) {
  return (
    <StepLayout
      title="Сън"
      explainer="Сънят е най-силният фактор за възстановяване. При недоспиване тренировки са с по-малък обем."
    >
      <NumberField
        label="Средно часове сън"
        unit="ч"
        value={draft.sleep_hours ?? undefined}
        onChange={(sleep_hours) => update({ sleep_hours })}
      />

      <p className="label mt-4">Качество на съня</p>
      {SLEEP.map((option) => (
        <OptionCard
          key={option.value}
          option={option}
          selected={draft.sleep_quality === option.value}
          onSelect={() => update({ sleep_quality: option.value as StepProps['draft']['sleep_quality'] })}
        />
      ))}

      <NumberField
        label="Кофеин на ден (по избор)"
        unit="мг"
        placeholder="едно кафе ≈ 90 мг"
        value={draft.caffeine_mg_per_day ?? undefined}
        onChange={(caffeine_mg_per_day) => update({ caffeine_mg_per_day })}
        integer
        hint="Помага да преценим дали кофеинът пречи на съня ти."
      />
    </StepLayout>
  )
}
