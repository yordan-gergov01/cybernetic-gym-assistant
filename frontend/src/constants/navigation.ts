/** Bottom-tab destinations. Order is thumb-priority: the screen used mid-workout is first. */
export type NavItem = { to: string; label: string; icon: string }

export const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Днес', icon: 'dumbbell' },
  { to: '/nutrition', label: 'Храна', icon: 'utensils' },
  { to: '/progress', label: 'Прогрес', icon: 'trending' },
  { to: '/coach', label: 'Треньор', icon: 'chat' },
]

/** Human names for the split the backend stores as a machine value. Unknown values fall
 *  through unchanged rather than being hidden. */
export const SPLIT_LABELS: Record<string, string> = {
  full_body: 'Full body',
  upper_lower: 'Горна/Долна',
  upper_lower_full: 'Горна/Долна + Full body',
  ppl: 'Push/Pull/Legs',
}

export const splitLabel = (value: string | null | undefined): string =>
  value ? (SPLIT_LABELS[value] ?? value) : ''
