import type { Option } from '../../../components/ui'

export const ACTIVITY: Option[] = [
  { value: 'sedentary', label: 'Заседнал', hint: 'офис работа и обичайни домашни задачи' },
  { value: 'light', label: 'Леко активен', hint: 'напр. дълго пътуване с колело' },
  { value: 'moderate', label: 'Умерено активен', hint: 'на крак голяма част от деня' },
  { value: 'active', label: 'Активен', hint: 'напр. личен треньор, цял ден на крак' },
  { value: 'very_active', label: 'Много активен', hint: 'физически труд' },
]

export const STRESS: Option[] = [
  { value: 'stress_free', label: 'Без стрес', hint: 'напр. в отпуск или пенсия' },
  { value: 'mild', label: 'Лек/периодичен', hint: 'напр. студент извън изпитни сесии' },
  { value: 'average', label: 'Среден', hint: 'работа на пълен ден с пътуване' },
  { value: 'high', label: 'Висок', hint: 'бързо темпо и голяма отговорност' },
]

export const SLEEP: Option[] = [
  { value: 'poor', label: 'Лошо', hint: 'будя се често, ставам неотпочинал' },
  { value: 'fair', label: 'Средно', hint: 'горе-долу, с колебания' },
  { value: 'good', label: 'Добро', hint: 'спя непрекъснато и ставам отпочинал' },
]
