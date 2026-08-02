import { Icon } from './Icon'

/** A single choice: the stored value, what the user reads, and why it matters. */
export type Option<T extends string = string> = { value: T; label: string; hint?: string }

/** Big tappable choice card - never a native select, which is unusable one-handed. */
export function OptionCard({
  option,
  selected,
  onSelect,
}: {
  option: Option
  selected: boolean
  onSelect: () => void
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={`tap flex w-full items-start gap-3 rounded-2xl border p-4 text-left ${
        selected ? 'border-volt-500 bg-volt-500/10' : 'border-ink-700 bg-ink-800'
      }`}
    >
      <span
        className={`mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full border-2 ${
          selected ? 'border-volt-500 bg-volt-500 text-ink-950' : 'border-ink-600'
        }`}
      >
        {selected && <Icon name="check" size={12} />}
      </span>
      <span className="min-w-0">
        <span className="block font-semibold text-chalk-50">{option.label}</span>
        {option.hint && <span className="mt-0.5 block text-sm text-chalk-500">{option.hint}</span>}
      </span>
    </button>
  )
}
