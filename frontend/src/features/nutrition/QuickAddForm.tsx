import { useState, type SubmitEvent } from 'react'
import { Icon } from '../../components/ui'

/** Free-text entry - the backend parses it (LLM + USDA), so the user types the way
 *  they'd say it: "2 яйца и 100г овес". */
export function QuickAddForm({ onSubmit, isPending }: { onSubmit: (text: string) => void; isPending: boolean }) {
  const [text, setText] = useState('')

  function handleSubmit(event: SubmitEvent) {
    event.preventDefault()
    const value = text.trim()
    if (!value) return
    onSubmit(value)
    setText('')
  }

  return (
    <form onSubmit={handleSubmit} className="mb-4 flex gap-2">
      <input
        className="input flex-1"
        placeholder="напр. 2 яйца, 100г овесени ядки"
        value={text}
        onChange={(e) => setText(e.target.value)}
        aria-label="Опиши какво си ял"
      />
      <button
        type="submit"
        className="btn-primary aspect-square px-0"
        disabled={!text.trim() || isPending}
        aria-label="Добави храна"
      >
        {isPending ? (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-ink-950/30 border-t-ink-950" />
        ) : (
          <Icon name="plus" size={20} />
        )}
      </button>
    </form>
  )
}
