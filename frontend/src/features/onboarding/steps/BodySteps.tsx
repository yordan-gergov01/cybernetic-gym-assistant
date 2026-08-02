import { Icon } from '../../../components/ui'
import { BfPhotoCapture } from '../BfPhotoCapture'
import { NumberField, OptionCard, StepLayout } from '../components'
import type { StepProps } from '../types'

export function WelcomeStep({ draft }: StepProps) {
  return (
    <StepLayout
      title="Да те опознаем"
      explainer="Ще ти зададем няколко въпроса, за да сметнем точните ти калории, макроси и да изготвим програма. Отговаряй честно - от това зависи колко добър ще е планът."
    >
      <div className="flex flex-col items-center gap-4 py-6">
        <span className="grid h-20 w-20 place-items-center rounded-3xl bg-volt-500/10 text-volt-400">
          <Icon name="sparkles" size={36} />
        </span>
        <p className="text-center text-sm text-chalk-500">
          Отнема около 5 минути. Можеш да се върнеш назад по всяко време.
        </p>
        {draft.age && (
          <p className="text-center text-xs text-chalk-500">Имаш започнати отговори - ще продължим оттам.</p>
        )}
      </div>
    </StepLayout>
  )
}

export function BasicsStep({ draft, update }: StepProps) {
  return (
    <StepLayout
      title="Основни данни"
      explainer="От тях се изчислява чистата ти телесна маса и базовият метаболизъм."
    >
      <div className="grid grid-cols-2 gap-3">
        {(['male', 'female'] as const).map((sex) => (
          <OptionCard
            key={sex}
            option={{ value: sex, label: sex === 'male' ? 'Мъж' : 'Жена' }}
            selected={draft.sex === sex}
            onSelect={() => update({ sex })}
          />
        ))}
      </div>

      <NumberField label="Възраст" unit="г." value={draft.age} onChange={(age) => update({ age })} />
      <NumberField
        label="Височина"
        unit="см"
        value={draft.height_cm}
        onChange={(height_cm) => update({ height_cm })}
      />
      <NumberField
        label="Тегло"
        unit="кг"
        value={draft.bodyweight_kg}
        onChange={(bodyweight_kg) => update({ bodyweight_kg })}
      />
    </StepLayout>
  )
}

export function BodyFatStep({ draft, update }: StepProps) {
  const method = draft.bf_method
  return (
    <StepLayout
      title="Процент телесни мазнини"
      explainer="Оттук зависят макросите за диетата ти. Визуалната оценка по снимки е по-точна от формула по BMI."
    >
      <OptionCard
        option={{ value: 'known', label: 'Знам го точно', hint: 'от калипер, DXA или InBody' }}
        selected={method === 'known'}
        onSelect={() => update({ bf_method: 'known' })}
      />
      {method === 'known' && (
        <NumberField
          label="Телесни мазнини"
          unit="%"
          value={draft.body_fat_pct ?? undefined}
          onChange={(body_fat_pct) => update({ body_fat_pct })}
        />
      )}

      <OptionCard
        option={{ value: 'photos', label: 'Ще кача снимки сега', hint: 'AI ще оцени по визуалния справочник на курса' }}
        selected={method === 'photos'}
        onSelect={() => update({ bf_method: 'photos', body_fat_pct: undefined })}
      />
      {method === 'photos' && <BfPhotoCapture draft={draft} update={update} />}

      <OptionCard
        option={{ value: 'unknown', label: 'Не знам', hint: 'ще изчислим приблизително по BMI' }}
        selected={method === 'unknown'}
        onSelect={() =>
          update({ bf_method: 'unknown', body_fat_pct: undefined, bf_assessment: undefined })
        }
      />
    </StepLayout>
  )
}
