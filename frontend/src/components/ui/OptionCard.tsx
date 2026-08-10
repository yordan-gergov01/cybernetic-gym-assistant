import type { ReactNode } from 'react'

/** A single choice: the stored value, what the user reads, and why it matters. */
export type Option<T extends string = string> = { value: T; label: string; hint?: string }

/** Big tappable choice card - never a native select, which is unusable one-handed.
 *
 *  Selection is carried by the border, the tint and the label colour together, so the
 *  card does not need a control glued to its side. The whole card is the target. */
export function OptionCard({
  option,
  selected,
  onSelect,
  icon,
}: {
  option: Option
  selected: boolean
  onSelect: () => void
  icon?: ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={`tap flex w-full items-center gap-3 rounded-2xl border p-4 text-left ${
        selected ? 'border-volt-500 bg-volt-500/8' : 'border-ink-700 bg-ink-800'
      }`}
    >
      {icon && (
        <span className={`shrink-0 ${selected ? 'text-volt-500' : 'text-chalk-300'}`}>{icon}</span>
      )}
      <span className="min-w-0">
        <span className={`block font-semibold ${selected ? 'text-volt-400' : 'text-chalk-50'}`}>
          {option.label}
        </span>
        {option.hint && (
          <span className="mt-0.5 block text-[13px] text-chalk-500">{option.hint}</span>
        )}
      </span>
    </button>
  )
}
