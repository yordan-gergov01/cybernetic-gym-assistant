import { LoginForm } from '../features/auth/LoginForm'

export function LoginPage() {
  return (
    <div className="flex min-h-dvh flex-col justify-center px-6 py-12">
      <div className="mx-auto w-full max-w-sm">
        <div className="mb-10 text-center">
          <div className="font-display text-[2.75rem] leading-none font-bold tracking-tight text-volt-400 uppercase">
            Cybernetic
          </div>
          <div className="mt-1 font-display text-xl font-semibold tracking-[0.4em] text-chalk-300 uppercase">
            Gym
          </div>
          <p className="mt-4 text-sm leading-relaxed text-chalk-500">
            Твоят научно-обоснован и обучен AI треньор
          </p>
        </div>

        <LoginForm />
      </div>
    </div>
  )
}
