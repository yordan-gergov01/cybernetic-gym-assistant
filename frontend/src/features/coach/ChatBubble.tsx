const typeDelay = [0, 150, 300]

export function ChatBubble({ role, content }: { role: string; content: string }) {
  const isUser = role === 'user'
  return (
    <div
      className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
        isUser
          ? 'ml-auto rounded-br-md bg-volt-500 font-medium text-ink-950'
          : 'mr-auto rounded-bl-md border border-ink-700 bg-ink-800 text-chalk-50'
      }`}
    >
      {content}
    </div>
  )
}


export function TypingBubble() {
  return (
    <div className="mr-auto flex gap-1.5 rounded-2xl rounded-bl-md border border-ink-700 bg-ink-800 px-4 py-4">
      {typeDelay.map((delay) => (
        <span
          key={delay}
          className="h-1.5 w-1.5 animate-bounce rounded-full bg-chalk-500"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </div>
  )
}
