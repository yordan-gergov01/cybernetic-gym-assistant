import { Link } from 'react-router-dom'
import { Callout } from '../components/ui'
import { AuthLayout } from '../features/auth/AuthLayout'
import { LoginForm } from '../features/auth/LoginForm'
import { useAuth } from '../features/auth/useAuth'

export function LoginPage() {
  const { sessionExpired } = useAuth()

  return (
    <AuthLayout
      eyebrow={sessionExpired ? 'Сесията изтече' : 'Добре дошъл обратно'}
      title="Влез"
      footer={
        <p className="text-center text-sm text-chalk-500">
          Нямаш профил?{' '}
          <Link to="/register" className="font-semibold text-volt-400">
            Създай профил
          </Link>
        </p>
      }
    >
      {sessionExpired && (
        <div className="mb-5">
          <Callout tone="warn" title="Влез отново">
            Влизането ти е изтекло. Нищо не е загубено — попълненото от настройката е
            запазено на устройството и ще продължи оттам.
          </Callout>
        </div>
      )}
      <LoginForm />
    </AuthLayout>
  )
}
