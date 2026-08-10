import { Link } from 'react-router-dom'
import { AuthLayout } from '../features/auth/AuthLayout'
import { RegisterForm } from '../features/auth/RegisterForm'

export function RegisterPage() {
  return (
    <AuthLayout
      eyebrow="Стъпка 1 от 2"
      title="Създай профил"
      intro="Първо профилът, после настройката, от която излизат целите ти."
      footer={
        <p className="text-center text-sm text-chalk-500">
          Вече имаш профил?{' '}
          <Link to="/login" className="font-semibold text-volt-400">
            Влез
          </Link>
        </p>
      }
    >
      <RegisterForm />
    </AuthLayout>
  )
}
