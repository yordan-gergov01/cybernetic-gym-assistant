/** Wizard option sets.
 *
 * Wording and grouping follow the Henselmans PT client intake form - the descriptions
 * are the concrete examples the form uses ("office job with standard life chores"),
 * because a vague label makes people pick the wrong bucket and skews every downstream
 * calculation. */

export type Option<T extends string = string> = { value: T; label: string; hint?: string }

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

export const TRAINING_STATUS: Option[] = [
  { value: '1', label: 'Начинаещ', hint: 'под 1 година последователни тренировки' },
  { value: '2', label: 'Средно напреднал', hint: '1–3 години' },
  { value: '3', label: 'Напреднал', hint: 'над 3 години' },
]

export const EQUIPMENT: Option[] = [
  { value: 'full_gym', label: 'Пълноценна зала', hint: 'щанги, машини, скрипци' },
  { value: 'home_gym', label: 'Домашна зала', hint: 'щанга и основни уреди' },
  { value: 'dumbbells_only', label: 'Само дъмбели' },
  { value: 'bodyweight', label: 'Само собствено тегло' },
]

/** The equipment checklist from the intake form - each item changes which exercises
 *  can be prescribed. */
export const EQUIPMENT_CHECKLIST: Option[] = [
  { value: 'squat_rack', label: 'Клетка или стойка за клек' },
  { value: 'hyperextension_bench', label: 'Пейка за хиперекстензии (45°)' },
  { value: 'glute_ham_raise', label: 'Glute-ham raise' },
  { value: 'dip_belt', label: 'Колан за набирания/дипове' },
  { value: 'leg_curl', label: 'Машина за задно бедро' },
  { value: 'leg_extension', label: 'Машина за преден бедрен мускул' },
  { value: 'cable_tower', label: 'Скрипец (кабелна кула)' },
  { value: 'seated_calf_raise', label: 'Машина за прасци седнал' },
  { value: 'rings', label: 'Гимнастически халки' },
  { value: 'trx', label: 'TRX / окачваща система' },
  { value: 'bands', label: 'Ластици за силов трибой' },
  { value: 'chains', label: 'Вериги' },
  { value: 'knee_wraps', label: 'Наколенки (wraps)' },
  { value: 'calipers', label: 'Калипер за кожни гънки' },
]

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

/** Asked as weight × reps, exactly as the intake form does. */
export const STRENGTH_LIFTS = [
  'Barbell Bench Press',
  'Barbell Squat',
  'Deadlift',
  'Overhead Press',
  'Barbell Row',
  'Pull-up',
] as const

export const BARBELL_INCREMENTS: Option[] = [
  { value: '1', label: '1 кг', hint: 'микро-дискове по 0.5 кг' },
  { value: '2.5', label: '2.5 кг', hint: 'най-леки дискове 1.25 кг' },
  { value: '5', label: '5 кг', hint: 'най-леки дискове 2.5 кг' },
  { value: '10', label: '10 кг', hint: 'най-леки дискове 5 кг' },
]

export const DUMBBELL_INCREMENTS: Option[] = [
  { value: '1', label: '1 кг' },
  { value: '2', label: '2 кг' },
  { value: '2.5', label: '2.5 кг' },
  { value: '5', label: '5 кг' },
]

export const DIETARY: Option[] = [
  { value: 'none', label: 'Няма' },
  { value: 'vegetarian', label: 'Вегетарианец' },
  { value: 'vegan', label: 'Веган' },
  { value: 'lactose_free', label: 'Без лактоза' },
  { value: 'gluten_free', label: 'Без глутен' },
  { value: 'keto', label: 'Кето' },
]
