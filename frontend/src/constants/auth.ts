/** Password rules, in one place because three screens set a password: registration,
 *  the reset link, and the change form inside the profile.
 *
 *  These mirror the backend schema (`UserRegister`, `ResetPasswordRequest`,
 *  `ChangePasswordRequest`) — the API is what enforces them; stating them here only
 *  means the user reads the requirement before typing rather than after submitting. */
export const MIN_PASSWORD_LENGTH = 8

/** Shown under a password field, so the wording cannot drift between the three forms. */
export const PASSWORD_HINT_BG = `Поне ${MIN_PASSWORD_LENGTH} знака`
