import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Icon } from './Icon'

type ListRowProps = {
  /** Index number or icon shown before the title. */
  leading?: ReactNode
  title: ReactNode
  subtitle?: ReactNode
  /** Badge, value or anything that belongs at the end of the row. */
  trailing?: ReactNode
  /** Show the chevron that marks a row as opening something. */
  chevron?: boolean
  to?: string
  onClick?: () => void
  /** Left edge accent — used for unread notifications. */
  accent?: boolean
}

function Body({ leading, title, subtitle, trailing, chevron }: ListRowProps) {
  return (
    <>
      {leading !== undefined && (
        <span className="grid w-6 shrink-0 place-items-center text-chalk-500">{leading}</span>
      )}
      <span className="min-w-0 flex-1">
        <span className="block truncate font-semibold text-chalk-50">{title}</span>
        {subtitle && <span className="mt-0.5 block text-sm text-chalk-500">{subtitle}</span>}
      </span>
      {trailing}
      {chevron && <Icon name="chevronRight" size={18} className="shrink-0 text-chalk-500" />}
    </>
  )
}

/** One line in a list: an exercise, a setting, a notification.
 *
 *  Renders as a link, a button or a plain row depending on what it does, so a row that
 *  goes nowhere is not announced to a screen reader as if it were tappable. */
export function ListRow(props: ListRowProps) {
  const { to, onClick, accent } = props
  const className = `row ${accent ? 'border-l-2 border-l-volt-500' : ''}`

  if (to) {
    return (
      <Link to={to} className={className}>
        <Body {...props} />
      </Link>
    )
  }
  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={className}>
        <Body {...props} />
      </button>
    )
  }
  return (
    <div className={className}>
      <Body {...props} />
    </div>
  )
}
