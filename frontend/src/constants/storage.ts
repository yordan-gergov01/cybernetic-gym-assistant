/** Everything this app keeps on the device, named in one place.
 *
 *  They were spread across three modules, all guessing at the same `cga_` prefix. A
 *  rename or a collision between them is silent - the app simply stops finding what it
 *  wrote - so the keys are declared together where a clash is visible. */
export const STORAGE_KEYS = {
  /** JWT for the API. Cleared on logout and whenever the API rejects it. */
  token: 'cga_token',
  /** Display name, so the profile has something to show before /auth/me answers. */
  name: 'cga_name',
  /** The unfinished onboarding form. Deliberately survives a logout: it is the user's
   *  own unsaved work. */
  onboardingDraft: 'cga_onboarding_draft',
} as const
