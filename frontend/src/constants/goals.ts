/** Short Bulgarian names for the goal the backend stores as a machine value.
 *
 *  Deliberately shorter than the onboarding labels: there the user is choosing and
 *  needs the explanation, here the goal is one item in a header line that also carries
 *  the week count and the training frequency. */
export const GOAL_LABELS: Record<string, string> = {
  bulk: 'Покачване',
  cut: 'Сваляне',
  aggressive_cut: 'Агресивно сваляне',
  maintain: 'Поддържане',
}

/** Unknown values fall through unchanged rather than being hidden. */
export const goalLabel = (value: string | null | undefined): string =>
  value ? (GOAL_LABELS[value] ?? value) : ''
