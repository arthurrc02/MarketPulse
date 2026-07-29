import { AnimatePresence, motion } from 'framer-motion'
import type { ComponentType } from 'react'
import { NavLink } from 'react-router-dom'

import {
  AnalyticsIcon,
  DashboardIcon,
  InsightsIcon,
  SettingsIcon,
  UploadsIcon,
  type IconProps,
} from '@/components/icons/Icons'
import { Logo } from '@/components/ui/Logo'

interface NavItem {
  to: string
  label: string
  icon: ComponentType<IconProps>
  end?: boolean
}

const NAV_ITEMS: NavItem[] = [
  { to: '/app', label: 'Dashboard', icon: DashboardIcon, end: true },
  { to: '/app/uploads', label: 'Uploads', icon: UploadsIcon },
  { to: '/app/analytics', label: 'Analytics', icon: AnalyticsIcon },
  { to: '/app/insights', label: 'Insights', icon: InsightsIcon },
  { to: '/app/settings', label: 'Configurações', icon: SettingsIcon },
]

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

/**
 * Coluna fixa em telas grandes; vira uma gaveta deslizante (com backdrop) em
 * telas menores, controlada pelo botão de menu do `Header`.
 */
export function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-40 bg-black/60 lg:hidden"
            onClick={onClose}
            aria-hidden="true"
            data-testid="sidebar-backdrop"
          />
        )}
      </AnimatePresence>
      <aside
        className={[
          'bg-surface-sunken border-border fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r transition-transform duration-200 ease-out lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full',
        ].join(' ')}
      >
        <div className="flex h-16 shrink-0 items-center px-6">
          <Logo />
        </div>
        <nav
          aria-label="Principal"
          className="flex flex-1 flex-col gap-1 overflow-y-auto px-3 py-2"
        >
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end ?? false}
              onClick={onClose}
              className={({ isActive }) =>
                [
                  'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-content-muted hover:bg-surface-elevated hover:text-content',
                ].join(' ')
              }
            >
              <Icon className="h-5 w-5 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  )
}
