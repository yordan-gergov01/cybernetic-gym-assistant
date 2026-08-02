import type { Option } from '../../../components/ui'

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

/** Days and session lengths offered as taps instead of a number field - the useful
 *  answers are few and typing one on a phone is slower than picking it. */
export const TRAINING_DAYS = [1, 2, 3, 4, 5, 6, 7]
export const SESSION_MINUTES = [45, 60, 75, 90, 120]
