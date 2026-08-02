import {
  BARBELL_INCREMENTS,
  DUMBBELL_INCREMENTS,
  EQUIPMENT,
  EQUIPMENT_CHECKLIST,
  STRENGTH_LIFTS,
  TRAINING_STATUS,
} from '../constants'
import { Chip, Field, NumberField, NumericInput, OptionCard, StepLayout, TextField } from '../components'
import { estimate1RM } from '../../../utils/strength'
import type { StepProps } from '../types'

export function ExperienceStep({ draft, update }: StepProps) {
  return (
    <StepLayout
      title="Тренировъчен опит"
      explainer="Нивото определя оптималния седмичен обем за всяка мускулна група."
    >
      {TRAINING_STATUS.map((option) => (
        <OptionCard
          key={option.value}
          option={option}
          selected={String(draft.training_status) === option.value}
          onSelect={() => update({ training_status: Number(option.value) as 1 | 2 | 3 })}
        />
      ))}
      <NumberField
        label="Години последователни тренировки"
        unit="г."
        value={draft.training_years}
        onChange={(training_years) => update({ training_years })}
      />
    </StepLayout>
  )
}

export function ScheduleStep({ draft, update }: StepProps) {
  return (
    <StepLayout
      title="График"
      explainer="Броят дни определя как се разпределя обемът. Часовете, в които не можеш, са също толкова важни - иначе ще получиш програма, която не можеш да следваш."
    >
      <Field label="Дни в залата седмично">
        <div className="flex gap-1.5">
          {[1, 2, 3, 4, 5, 6, 7].map((days) => (
            <button
              key={days}
              type="button"
              onClick={() => update({ training_days_per_week: days })}
              aria-pressed={draft.training_days_per_week === days}
              className={`tap num h-12 flex-1 rounded-xl border text-lg font-semibold ${
                draft.training_days_per_week === days
                  ? 'border-volt-500 bg-volt-500 text-ink-950'
                  : 'border-ink-700 bg-ink-800 text-chalk-300'
              }`}
            >
              {days}
            </button>
          ))}
        </div>
      </Field>

      <Field label="Време на тренировка">
        <div className="flex flex-wrap gap-2">
          {[45, 60, 75, 90, 120].map((min) => (
            <Chip
              key={min}
              label={`${min} мин`}
              selected={draft.session_duration_min === min}
              onToggle={() => update({ session_duration_min: min })}
            />
          ))}
        </div>
      </Field>

      <TextField
        label="Кога НЕ можеш да тренираш"
        placeholder="напр. делник преди 17:00; неделя целия ден"
        value={draft.unavailable_times ?? undefined}
        onChange={(unavailable_times) => update({ unavailable_times })}
        hint="Колкото по-конкретно, толкова по-изпълнима ще е програмата."
      />
    </StepLayout>
  )
}

export function EquipmentStep({ draft, update }: StepProps) {
  const details = draft.equipment_details ?? {}
  const toggle = (key: string) =>
    update({ equipment_details: { ...details, [key]: !details[key] } })

  return (
    <StepLayout title="Къде тренираш?" explainer="Определя кои упражнения изобщо могат да ти бъдат зададени.">
      {EQUIPMENT.map((option) => (
        <OptionCard
          key={option.value}
          option={option}
          selected={draft.available_equipment === option.value}
          onSelect={() =>
            update({ available_equipment: option.value as StepProps['draft']['available_equipment'] })
          }
        />
      ))}

      <div className="pt-2">
        <p className="label">С какво разполагаш?</p>
        <div className="flex flex-wrap gap-2">
          {EQUIPMENT_CHECKLIST.map((item) => (
            <Chip
              key={item.value}
              label={item.label}
              selected={!!details[item.value]}
              onToggle={() => toggle(item.value)}
            />
          ))}
        </div>
      </div>
    </StepLayout>
  )
}

export function IncrementsStep({ draft, update }: StepProps) {
  return (
    <StepLayout
      title="Най-малките стъпки в тежестта"
      explainer="Прогресията ти се изчислява спрямо това. Ако най-леките дискове позволяват само 5 кг скок, няма смисъл да ти пишем +2.5 кг."
    >
      <p className="label">Най-малък скок с щанга</p>
      {BARBELL_INCREMENTS.map((option) => (
        <OptionCard
          key={option.value}
          option={option}
          selected={draft.min_barbell_increment_kg === Number(option.value)}
          onSelect={() => update({ min_barbell_increment_kg: Number(option.value) })}
        />
      ))}

      <p className="label mt-4">Стъпка между дъмбелите</p>
      <div className="flex flex-wrap gap-2">
        {DUMBBELL_INCREMENTS.map((option) => (
          <Chip
            key={option.value}
            label={option.label}
            selected={draft.min_dumbbell_increment_kg === Number(option.value)}
            onToggle={() => update({ min_dumbbell_increment_kg: Number(option.value) })}
          />
        ))}
      </div>
    </StepLayout>
  )
}

export function StrengthStep({ draft, update }: StepProps) {
  const lifts = draft.lifts ?? {}

  const setLift = (name: string, field: 'weight' | 'reps', value: number | undefined) => {
    const current = lifts[name] ?? { weight: 0, reps: 0 }
    const nextLift = { ...current, [field]: value ?? 0 }
    const next = { ...lifts, [name]: nextLift }
    if (!nextLift.weight && !nextLift.reps) delete next[name]
    update({ lifts: next })
  }

  return (
    <StepLayout
      title="Текущите ти постижения"
      explainer="Опиши за всяко от упражненията какви са ти ТОП сериите (напр. лежанка най-много съм пробвал със 100кг. за 3 повторения)"
    >
      {STRENGTH_LIFTS.map((name) => {
        const lift = lifts[name]
        const oneRm = lift?.weight && lift?.reps ? estimate1RM(lift.weight, lift.reps) : null
        return (
          <div key={name} className="card">
            <p className="mb-2 font-semibold">{name}</p>
            <div className="flex items-center gap-2">
              <NumericInput
                value={lift?.weight || undefined}
                onChange={(weight) => setLift(name, 'weight', weight)}
                placeholder="кг"
                ariaLabel={`${name} - тежест в килограми`}
                className="input num h-11 min-h-0 flex-1 text-center font-semibold"
              />
              <span className="text-chalk-500">×</span>
              <NumericInput
                value={lift?.reps || undefined}
                onChange={(reps) => setLift(name, 'reps', reps)}
                integer
                placeholder="повт."
                ariaLabel={`${name} - брой повторения`}
                className="input num h-11 min-h-0 flex-1 text-center font-semibold"
              />
            </div>
            {oneRm && <p className="num mt-2 text-sm text-volt-400">≈ 1ПМ: {oneRm} кг</p>}
          </div>
        )
      })}
    </StepLayout>
  )
}
