import { Link } from 'react-router-dom'
import { Icon, type IconName } from '../components/ui'

const PROMISES: { icon: IconName; title: string; body: string }[] = [
  {
    icon: 'target',
    title: 'План, смятан за теб',
    body: 'Калории, макроси и седмичен обем излизат от твоите мерки, състав и график - не от таблица за среден човек.',
  },
  {
    icon: 'trending',
    title: 'Прогресия всяка сесия',
    body: 'Следващата тежест се изчислява от последната ти серия. Никакво налучкване колко да сложиш.',
  },
  {
    icon: 'sparkles',
    title: 'Треньор, който обяснява',
    body: 'Всеки отговор стъпва на научно-обоснована методология и ти казва защо, а не само какво.',
  },
]

/** First screen a new user sees.
 *
 *  It has one job: say what the product decides for you, in one breath, and offer a
 *  single way forward. The headline carries the whole premise - training is measured,
 *  not felt - because that is what separates this from a workout log. */
export function LandingPage() {
  return (
    <div className="flex min-h-dvh flex-col bg-ink-950">
      <main className="flex-1 px-6" style={{ paddingTop: 'calc(env(safe-area-inset-top) + 40px)' }}>
        <div className="mx-auto w-full max-w-md">
          <div className="flex items-center gap-2">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-volt-500 text-ink-950">
              <Icon name="dumbbell" size={20} />
            </span>
            <span className="font-display text-lg font-bold tracking-[0.2em] uppercase">
              Cybernetic
            </span>
          </div>

          <h1 className="mt-10 font-display text-[2.75rem] leading-[0.95] font-bold tracking-tight uppercase">
            Прогресът не се
            <br />
            усеща.
            <br />
            <span className="text-volt-400">Измерва се.</span>
          </h1>

          <p className="mt-5 text-base leading-relaxed text-chalk-300">
            Персонален AI треньор, който смята програмата и храненето ти от реалните ти
            числа и ги преизчислява всяка седмица според това, което си направил в залата.
          </p>

          <ul className="mt-10 space-y-3">
            {PROMISES.map((promise) => (
              <li key={promise.title} className="card flex gap-3">
                <span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-volt-500/10 text-volt-400">
                  <Icon name={promise.icon} size={18} />
                </span>
                <span className="min-w-0">
                  <span className="block font-semibold text-chalk-50">{promise.title}</span>
                  <span className="mt-1 block text-sm leading-relaxed text-chalk-500">
                    {promise.body}
                  </span>
                </span>
              </li>
            ))}
          </ul>

          <p className="mt-8 text-center text-xs leading-relaxed text-chalk-500">
            Настройката отнема около 5 минути и от нея излизат първите ти цели.
          </p>
        </div>
      </main>

      {/* The two actions sit in a fixed bar: on a phone this screen scrolls, and the way
          forward must never be the thing you have to scroll to find. */}
      <div
        className="sticky bottom-0 mt-8 border-t border-ink-700 bg-ink-950/95 px-6 pt-4 backdrop-blur"
        style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 16px)' }}
      >
        <div className="mx-auto w-full max-w-md space-y-2">
          <Link to="/register" className="btn-primary w-full">
            Създай профил
          </Link>
          <Link to="/login" className="btn-outline w-full">
            Вече имам профил
          </Link>
        </div>
      </div>
    </div>
  )
}
