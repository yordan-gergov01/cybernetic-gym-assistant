/** Password rules, in one place because three screens set a password: registration,
 *  the reset link, and the change form inside the profile.
 *
 *  These mirror app/schemas.py (`UserRegister`, `ResetPasswordRequest`,
 *  `ChangePasswordRequest`) — the API is what enforces them; stating them here only
 *  means the user reads the requirement before typing rather than after submitting. */
export const MIN_PASSWORD_LENGTH = 8

/** What the password is missing, phrased for the user, or null when it is fine.
 *
 *  Same rules and the same sentence the API answers with, so a password rejected here
 *  and one rejected there do not read like two different problems. */
export function passwordProblem(password: string): string | null {
  const missing: string[] = []
  if (password.length < MIN_PASSWORD_LENGTH) missing.push(`поне ${MIN_PASSWORD_LENGTH} знака`)
  if (!/\p{L}/u.test(password)) missing.push('буква')
  if (!/\d/u.test(password)) missing.push('цифра')
  if (!/[^\p{L}\d\s]/u.test(password)) missing.push('специален знак (например ! ? # @)')
  if (missing.length === 0) return null
  const needs =
    missing.length === 1
      ? missing[0]
      : `${missing.slice(0, -1).join(', ')} и ${missing[missing.length - 1]}`
  return `Паролата трябва да съдържа ${needs}.`
}

/** Shown under a password field, so the wording cannot drift between the three forms. */
export const PASSWORD_HINT_BG = `Поне ${MIN_PASSWORD_LENGTH} знака, с буква, цифра и специален знак`
