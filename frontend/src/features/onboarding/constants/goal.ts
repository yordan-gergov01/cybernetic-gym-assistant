import type { Option } from '../../../components/ui'

export const GOALS: Option[] = [
  { value: 'bulk', label: 'Покачване на мускулна маса', hint: '≈ +0.25 кг/седмица' },
  { value: 'cut', label: 'Сваляне на мазнини', hint: '≈ −0.5 кг/седмица' },
  { value: 'aggressive_cut', label: 'Агресивно сваляне', hint: '≈ −0.75 кг/седмица' },
  { value: 'maintain', label: 'Поддържане', hint: 'тегло без промяна' },
]

export const DEDICATION: Option[] = [
  {
    value: 'sustainable',
    label: 'Устойчивост преди всичко',
    hint: 'Докато вървя в правилната посока, скоростта няма значение.',
  },
  {
    value: 'balanced',
    label: 'Разумен баланс',
    hint: 'Добри резултати спрямо вложеното усилие, но да е поносимо.',
  },
  {
    value: 'maximal',
    label: 'Максимален резултат',
    hint: 'Ще направя каквото е нужно, без да компрометирам здравето си.',
  },
]
