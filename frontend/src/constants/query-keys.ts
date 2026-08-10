/** Central TanStack Query keys, so invalidation after a mutation cannot drift out of
 *  sync with the key a screen actually queries under. */
export const queryKeys = {
  programs: ['programs'] as const,
  program: (id: string | undefined) => ['program', id] as const,
  workouts: ['workouts'] as const,
  today: ['workouts', 'today'] as const,
  nutrition: (date: string) => ['nutrition', date] as const,
  weightTrend: (days: number) => ['weight', 'trend', days] as const,
  strength: (weeks: number) => ['strength', weeks] as const,
  photos: ['photos'] as const,
  weightCoaching: ['weight', 'coaching'] as const,
  chat: ['chat'] as const,
  profile: ['profile'] as const,
}
