import { useState, type SubmitEvent } from 'react'

export function WeightForm({ onSubmit, isPending }: { onSubmit: (kg: number) => void; isPending: boolean }) {
  const [value, setValue] = useState('')

  function handleSubmit(event: SubmitEvent) {
    event.preventDefault()
    const kg = Number(value)
    if (!kg || Number.isNaN(kg)) return
    onSubmit(kg)
    setValue('')
  }

  return (
    <form onSubmit={handleSubmit} className="mb-4 flex gap-2">
      <input
        inputMode="decimal"
        className="input flex-1 font-display text-lg font-semibold tabular-nums"
        placeholder="Тегло днес (кг)"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        aria-label="Тегло днес в килограми"
      />
      <button type="submit" className="btn-primary px-6" disabled={!value || isPending}>
        {isPending ? '…' : 'Запиши'}
      </button>
    </form>
  )
}
