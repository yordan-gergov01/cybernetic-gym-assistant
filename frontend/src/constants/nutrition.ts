/** Macro rows shown on the nutrition screen, in the order a lifter cares about them. */
export type MacroKey = 'protein_g' | 'carbs_g' | 'fat_g'

export const MACROS: { key: MacroKey; label: string; unit: string; tone: 'ok' | 'accent' }[] = [
  { key: 'protein_g', label: 'Протеин', unit: 'г', tone: 'ok' },
  { key: 'carbs_g', label: 'Въглехидрати', unit: 'г', tone: 'accent' },
  { key: 'fat_g', label: 'Мазнини', unit: 'г', tone: 'accent' },
]
