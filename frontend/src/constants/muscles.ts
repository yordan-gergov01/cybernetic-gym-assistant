/** Bulgarian names for the muscle groups the API speaks in English.
 *
 *  One map for the whole app: the onboarding chips, the volume bars and the badge next
 *  to an exercise must never call the same muscle two different things. */
export const MUSCLE_LABELS: Record<string, string> = {
  chest: 'Гърди',
  back: 'Гръб',
  lats: 'Ламбовиден',
  shoulders: 'Рамене',
  rear_delts: 'Задни рамене',
  front_delts: 'Предни рамене',
  traps: 'Трапец',
  biceps: 'Бицепс',
  triceps: 'Трицепс',
  forearms: 'Предмишници',
  quads: 'Квадрицепс',
  hamstrings: 'Задно бедро',
  glutes: 'Седалище',
  calves: 'Прасци',
  adductors: 'Приводящи',
  abs: 'Корем',
  neck: 'Врат',
}

/** Falls back to the English name rather than hiding a muscle we have no label for. */
export const muscleLabel = (muscle: string | null | undefined): string =>
  muscle ? (MUSCLE_LABELS[muscle.toLowerCase()] ?? muscle) : ''

/** Order the onboarding chips and the volume list follow - large groups first, so the
 *  ones people actually prioritise are not buried under accessories. */
export const MUSCLE_ORDER = [
  'chest',
  'back',
  'shoulders',
  'biceps',
  'triceps',
  'quads',
  'hamstrings',
  'glutes',
  'calves',
  'abs',
  'rear_delts',
] as const
