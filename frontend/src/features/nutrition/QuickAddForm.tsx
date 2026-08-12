import { useState, type SubmitEvent } from 'react'

/** Free-text entry - the backend parses it (LLM + USDA), so the user types the way
 *  they'd say it: "2 яйца и 100г овес".
 *
 *  There is no voice or photo button here on purpose: nothing behind them exists yet,
 *  and a control that does nothing is worse than one that is missing. */
export function QuickAddForm({
  onSubmit,
  isPending,
}: {
  onSubmit: (text: string) => void
  isPending: boolean
}) {
  const [text, setText] = useState('')

  function handleSubmit(event: SubmitEvent) {
    event.preventDefault()
    const value = text.trim()
    if (!value) return
    onSubmit(value)
    setText('')
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        className="input"
        placeholder="напр. 2 яйца, 100г овесени ядки"
        value={text}
        onChange={(e) => setText(e.target.value)}
        aria-label="Опиши какво си ял"
      />
      <button
        type="submit"
        className="btn-primary mt-2 w-full"
        disabled={!text.trim() || isPending}
      >
        {isPending ? 'Разчитаме…' : 'Добави'}
      </button>
    </form>
  )
}
