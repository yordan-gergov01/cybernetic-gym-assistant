import type { ReactNode } from 'react'

/** Heading that opens a block of content, optionally with one action on the right
 *  ("Виж всички", "Отбележи всички"). */
export function SectionHeader({ title, action }: { title: string; action?: ReactNode }) {
  return (
    <div className="mt-8 mb-3 flex items-end justify-between gap-3">
      <h2 className="section-title text-chalk-50">{title}</h2>
      {action}
    </div>
  )
}
