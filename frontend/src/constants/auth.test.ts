import { describe, expect, it } from 'vitest'
import { PASSWORD_HINT_BG, passwordProblem } from './auth'

/** The rule is enforced by the API; what these guard is that the screen rejects the same
 *  passwords with the same words, so a user who fixes what the form asked for does not
 *  then get a second, differently worded refusal from the server. */
describe('passwordProblem', () => {
  it('accepts a password with a letter, a digit and a symbol', () => {
    expect(passwordProblem('Parola1!')).toBeNull()
  })

  it.each([
    ['12345678', 'буква'],
    ['password!', 'цифра'],
    ['Password1', 'специален знак'],
    ['krat1!', 'поне 8 знака'],
  ])('tells the user what %s is missing', (password, missing) => {
    expect(passwordProblem(password)).toContain(missing)
  })

  it('does not count a space as the special character', () => {
    expect(passwordProblem('parola 1234')).toContain('специален знак')
  })

  it('names every missing rule at once rather than one per attempt', () => {
    const problem = passwordProblem('12345678')
    expect(problem).toContain('буква')
    expect(problem).toContain('специален знак')
  })

  it('states the rule in the hint the forms show', () => {
    expect(PASSWORD_HINT_BG).toContain('8')
    expect(PASSWORD_HINT_BG).toContain('специален знак')
  })
})
