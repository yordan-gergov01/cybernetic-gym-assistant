import { Chip, TextField } from '../../../components/ui'
import { DIETARY, MAX_PRIORITY_MUSCLES, MUSCLES } from '../constants'
import { StepLayout } from '../components'
import type { StepProps } from '../types'

export function FocusStep({ draft, update }: StepProps) {
  const priority = draft.priority_muscles ?? []
  const avoid = draft.avoid_growth_muscles ?? []

  const togglePriority = (value: string) => {
    const next = priority.includes(value) ? priority.filter((m) => m !== value) : [...priority, value]
    update({ priority_muscles: next, avoid_growth_muscles: avoid.filter((m) => !next.includes(m)) })
  }

  const toggleAvoid = (value: string) => {
    const next = avoid.includes(value) ? avoid.filter((m) => m !== value) : [...avoid, value]
    update({ avoid_growth_muscles: next, priority_muscles: priority.filter((m) => !next.includes(m)) })
  }

  return (
    <StepLayout
      title="Приоритети"
      explainer="Приоритетните мускули получават повече серии седмично. Може да избереш до 3."
    >
      <p className="label">Искам да наблегна на</p>
      <div className="flex flex-wrap gap-2">
        {MUSCLES.map((muscle) => (
          <Chip
            key={muscle.value}
            label={muscle.label}
            selected={priority.includes(muscle.value)}
            onToggle={() => togglePriority(muscle.value)}
            disabled={priority.length >= MAX_PRIORITY_MUSCLES}
          />
        ))}
      </div>

      <p className="label mt-5">Не искам да растат</p>
      <div className="flex flex-wrap gap-2">
        {MUSCLES.map((muscle) => (
          <Chip
            key={muscle.value}
            label={muscle.label}
            selected={avoid.includes(muscle.value)}
            onToggle={() => toggleAvoid(muscle.value)}
          />
        ))}
      </div>

      <TextField
        label="Друг спорт или активност"
        placeholder="напр. футбол 1× седмично, йога"
        value={draft.other_activities ?? undefined}
        onChange={(other_activities) => update({ other_activities })}
        hint="Влияе на възстановяването и на общия обем."
        rows={2}
      />
    </StepLayout>
  )
}

export function LimitationsStep({ draft, update }: StepProps) {
  return (
    <StepLayout
      title="Травми и предпочитания"
      explainer="Ще избегнем движенията, които ти пречат, и ще заложим на тези, които предпочиташ и харесваш."
    >
      <TextField
        label="Травми, болки или заболявания"
        placeholder="напр. болка в лявото рамо при лежанка; дискова херния L4-L5"
        value={draft.injuries ?? undefined}
        onChange={(injuries) => update({ injuries })}
      />
      <TextField
        label="Упражнения, които предпочиташ или мразиш"
        placeholder="напр. обичам дъмбели, мразя бърпита"
        value={draft.exercise_preferences ?? undefined}
        onChange={(exercise_preferences) => update({ exercise_preferences })}
      />
      <TextField
        label="Текуща програма (по избор)"
        placeholder="напр. Upper/Lower 4 дни от 3 месеца"
        value={draft.current_program ?? undefined}
        onChange={(current_program) => update({ current_program })}
        rows={2}
      />
    </StepLayout>
  )
}

export function NutritionStep({ draft, update }: StepProps) {
  const selected = (draft.dietary_restrictions ?? '').split(',').map((s) => s.trim()).filter(Boolean)

  const toggle = (value: string) => {
    const next =
      value === 'none'
        ? ['none']
        : selected.includes(value)
          ? selected.filter((v) => v !== value)
          : [...selected.filter((v) => v !== 'none'), value]
    update({ dietary_restrictions: next.join(', ') })
  }

  return (
    <StepLayout
      title="Хранене"
      explainer="Ограниченията определят кои източници на протеин и въглехидрати ще предлагаме."
    >
      <div className="flex flex-wrap gap-2">
        {DIETARY.map((option) => (
          <Chip
            key={option.value}
            label={option.label}
            selected={selected.includes(option.value)}
            onToggle={() => toggle(option.value)}
          />
        ))}
      </div>

      <TextField
        label="Как се храниш сега (по избор)"
        placeholder="напр. 3 хранения, много въглехидрати вечер"
        value={draft.current_diet ?? undefined}
        onChange={(current_diet) => update({ current_diet })}
        rows={2}
      />
    </StepLayout>
  )
}
