/** Bottom-tab destinations. Order is thumb-priority: the screen used mid-workout is first. */
export type NavItem = { to: string; label: string; icon: string }

export const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Днес', icon: 'dumbbell' },
  { to: '/nutrition', label: 'Храна', icon: 'utensils' },
  { to: '/progress', label: 'Прогрес', icon: 'trending' },
  { to: '/coach', label: 'Треньор', icon: 'chat' },
]
