/** Multi-select chip, used for muscle groups and dietary tags. */
export function Chip({
  label,
  selected,
  onToggle,
  disabled,
}: {
  label: string
  selected: boolean
  onToggle: () => void
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={disabled && !selected}
      aria-pressed={selected}
      className={`tap min-h-11 rounded-xl border px-4 text-sm font-medium disabled:opacity-35 ${
        selected
          ? 'border-volt-500 bg-volt-500/8 text-volt-400'
          : 'border-ink-700 bg-ink-800 text-chalk-300'
      }`}
    >
      {label}
    </button>
  )
}
