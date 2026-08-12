/** Macro rows shown on the nutrition screen, in the order a lifter cares about them. */
export type MacroKey = 'protein_g' | 'carbs_g' | 'fat_g'

export const MACROS: { key: MacroKey; label: string; unit: string; tone: 'ok' | 'accent' }[] = [
  { key: 'protein_g', label: 'Протеин', unit: 'г', tone: 'ok' },
  { key: 'carbs_g', label: 'Въглехидрати', unit: 'г', tone: 'accent' },
  { key: 'fat_g', label: 'Мазнини', unit: 'г', tone: 'accent' },
]

/** Meals in the order they happen, so the day reads top to bottom. */
export const MEAL_ORDER = ['breakfast', 'lunch', 'dinner', 'snack'] as const
export type MealType = (typeof MEAL_ORDER)[number]

export const MEAL_LABELS: Record<string, string> = {
  breakfast: 'Закуска',
  lunch: 'Обяд',
  dinner: 'Вечеря',
  snack: 'Снакс',
}

/** Which meal an entry logged right now belongs to. People log as they eat, so the
 *  clock is a better guess than asking, and the grouping is only a heading. */
export function mealForHour(hour: number): MealType {
  if (hour < 11) return 'breakfast'
  if (hour < 16) return 'lunch'
  if (hour < 22) return 'dinner'
  return 'snack'
}
