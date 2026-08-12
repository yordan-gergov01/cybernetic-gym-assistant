import type { IconType } from 'react-icons'
import {
  LuBell,
  LuCalendarDays,
  LuCamera,
  LuCheck,
  LuChevronLeft,
  LuChevronRight,
  LuCircleAlert,
  LuDumbbell,
  LuFlame,
  LuInfo,
  LuMessageCircle,
  LuMoon,
  LuPlus,
  LuScale,
  LuSend,
  LuSettings,
  LuSparkles,
  LuTarget,
  LuTimer,
  LuTrash2,
  LuTrendingUp,
  LuUtensils,
  LuX,
} from 'react-icons/lu'

/** Icon registry. Screens reference glyphs by name, never by import, so the whole set
 *  can be swapped (or one glyph replaced) in a single place. Icons inherit
 *  `currentColor`, which is what lets the active nav tab tint volt.
 *
 *  Kept separate from the component so the module exports only constants and Fast
 *  Refresh keeps working for Icon.tsx. */
export const ICONS = {
  dumbbell: LuDumbbell,
  utensils: LuUtensils,
  trending: LuTrendingUp,
  chat: LuMessageCircle,
  check: LuCheck,
  send: LuSend,
  close: LuX,
  trash: LuTrash2,
  plus: LuPlus,
  calendar: LuCalendarDays,
  bell: LuBell,
  camera: LuCamera,
  scale: LuScale,
  flame: LuFlame,
  moon: LuMoon,
  timer: LuTimer,
  target: LuTarget,
  sparkles: LuSparkles,
  settings: LuSettings,
  info: LuInfo,
  alert: LuCircleAlert,
  chevronRight: LuChevronRight,
  chevronLeft: LuChevronLeft,
} satisfies Record<string, IconType>

export type IconName = keyof typeof ICONS
