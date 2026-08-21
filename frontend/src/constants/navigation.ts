/** Bottom-tab destinations. Order is thumb-priority: the screen used mid-workout is first. */
export type NavItem = { to: string; label: string; icon: string }

export const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Днес', icon: 'dumbbell' },
  { to: '/nutrition', label: 'Храна', icon: 'utensils' },
  { to: '/progress', label: 'Прогрес', icon: 'trending' },
  { to: '/coach', label: 'Треньор', icon: 'chat' },
]

/** Actions in the top-right of a tab screen. Declared here with the tabs, so the set of
 *  ways out of a screen is described in one place instead of per page.
 *
 *  Today carries the extra link to the program: it is the screen the plan is executed
 *  from, so it is where "show me the whole plan" belongs. */
export const HEADER_ACTIONS = {
  today: [
    { to: '/program', icon: 'calendar' as const, label: 'Програма' },
    { to: '/notifications', icon: 'bell' as const, label: 'Известия' },
    { to: '/profile', icon: 'settings' as const, label: 'Профил' },
  ],
  secondary: [
    { to: '/notifications', icon: 'bell' as const, label: 'Известия' },
    { to: '/profile', icon: 'settings' as const, label: 'Профил' },
  ],
}

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
