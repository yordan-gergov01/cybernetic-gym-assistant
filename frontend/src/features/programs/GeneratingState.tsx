import { useEffect, useState } from 'react'

/** Program generation takes 20–40s. A bare spinner reads as "broken", so the wait is
 *  narrated with the actual stages the backend goes through. */
const STAGES = [
  'Анализирам профила ти…',
  'Търся в материалите на Henselmans…',
  'Подбирам упражнения за оборудването ти…',
  'Изчислявам обема по мускулни групи…',
  'Подреждам прогресията по седмици…',
]

export function GeneratingState() {
  const [stage, setStage] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setStage((s) => Math.min(s + 1, STAGES.length - 1)), 6000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="card flex flex-col items-center gap-5 py-12 text-center">
      <span className="relative grid h-16 w-16 place-items-center">
        <span className="absolute inset-0 animate-spin rounded-full border-2 border-ink-700 border-t-volt-500" />
        <span className="num text-lg text-volt-400">AI</span>
      </span>
      <div>
        <p className="font-semibold text-chalk-50">Създавам програмата ти</p>
        <p className="mt-1.5 text-sm text-chalk-500">{STAGES[stage]}</p>
      </div>
      <p className="max-w-xs text-xs text-chalk-500">Отнема до минута. Не затваряй приложението.</p>
    </div>
  )
}
