import { MUSCLE_ORDER, muscleLabel } from '../../../constants/muscles'
import type { Option } from '../../../components/ui'

/** Built from the app-wide muscle map, so a label changed there changes here too. */
export const MUSCLES: Option[] = MUSCLE_ORDER.map((value) => ({ value, label: muscleLabel(value) }))

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
