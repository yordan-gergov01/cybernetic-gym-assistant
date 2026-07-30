import { NavLink } from 'react-router-dom'
import { NAV_ITEMS } from '../../constants/navigation'
import { Icon, type IconName } from '../ui'

/** Primary destinations sit in the thumb arc - the only comfortably reachable zone
 *  when the phone is held one-handed in the gym. */
export function BottomNav() {
  return (
    <nav className="safe-bottom fixed inset-x-0 bottom-0 z-40 border-t border-ink-700 bg-ink-900/95 backdrop-blur">
      <div className="mx-auto flex max-w-lg">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `tap flex min-h-[56px] flex-1 flex-col items-center justify-center gap-1 py-2 ${
                isActive ? 'text-volt-500' : 'text-chalk-500'
              }`
            }
          >
            <Icon name={item.icon as IconName} size={23} />
            <span className="text-[11px] font-medium tracking-wide">{item.label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
