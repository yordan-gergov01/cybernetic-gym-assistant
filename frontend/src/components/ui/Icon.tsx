import { ICONS, type IconName } from './icons'

export function Icon({ name, size = 22, className }: { name: IconName; size?: number; className?: string }) {
  const Glyph = ICONS[name]
  return <Glyph size={size} className={className} aria-hidden="true" />
}
