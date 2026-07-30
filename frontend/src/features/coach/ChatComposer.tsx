import { useState, type SubmitEvent } from 'react'
import { Icon } from '../../components/ui'

export function ChatComposer({ onSend, isPending }: { onSend: (text: string) => void; isPending: boolean }) {
  const [text, setText] = useState('')

  function handleSubmit(event: SubmitEvent) {
    event.preventDefault()
    const value = text.trim()
    if (!value) return
    onSend(value)
    setText('')
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        className="input flex-1"
        placeholder="Питай треньора…"
        value={text}
        onChange={(e) => setText(e.target.value)}
        aria-label="Съобщение до треньора"
      />
      <button
        type="submit"
        className="btn-primary aspect-square px-0"
        disabled={!text.trim() || isPending}
        aria-label="Изпрати"
      >
        <Icon name="send" size={20} />
      </button>
    </form>
  )
}
