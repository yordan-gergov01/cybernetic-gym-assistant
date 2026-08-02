import type { Option } from '../../../components/ui'

export const MUSCLES: Option[] = [
  { value: 'chest', label: 'Гърди' },
  { value: 'back', label: 'Гръб' },
  { value: 'shoulders', label: 'Рамене' },
  { value: 'biceps', label: 'Бицепс' },
  { value: 'triceps', label: 'Трицепс' },
  { value: 'quads', label: 'Квадрицепс' },
  { value: 'hamstrings', label: 'Задно бедро' },
  { value: 'glutes', label: 'Седалище' },
  { value: 'calves', label: 'Прасци' },
  { value: 'abs', label: 'Корем' },
  { value: 'rear_delts', label: 'Задни рамене' },
]

/** Spreading priority over more than three muscles leaves none of them with enough
 *  extra volume to matter. */
export const MAX_PRIORITY_MUSCLES = 3

export const DIETARY: Option[] = [
  { value: 'none', label: 'Няма' },
  { value: 'vegetarian', label: 'Вегетарианец' },
  { value: 'vegan', label: 'Веган' },
  { value: 'lactose_free', label: 'Без лактоза' },
  { value: 'gluten_free', label: 'Без глутен' },
  { value: 'keto', label: 'Кето' },
]
