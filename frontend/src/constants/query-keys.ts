/** Central TanStack Query keys, so invalidation after a mutation cannot drift out of
 *  sync with the key a screen actually queries under. */
export const queryKeys = {
  programs: ['programs'] as const,
  program: (id: string | undefined) => ['program', id] as const,
  programReview: (id: string | undefined) => ['program', id, 'review'] as const,
  workouts: ['workouts'] as const,
  today: ['workouts', 'today'] as const,
  /** Nested under `workouts` so logging a session invalidates it too. */
  workoutLogs: (limit: number) => ['workouts', 'logs', limit] as const,
  exercises: (filter: string) => ['exercises', 'list', filter] as const,
  exerciseCategories: ['exercises', 'categories'] as const,
  exerciseAlternatives: (name: string) => ['exercises', 'alternatives', name] as const,
  nutrition: (date: string) => ['nutrition', date] as const,
  weightTrend: (days: number) => ['weight', 'trend', days] as const,
  strength: (weeks: number) => ['strength', weeks] as const,
  photos: ['photos'] as const,
  weightCoaching: ['weight', 'coaching'] as const,
  chat: ['chat'] as const,
  profile: ['profile'] as const,
}
