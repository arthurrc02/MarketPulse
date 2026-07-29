import { AnimatePresence, motion } from 'framer-motion'
import {
  cloneElement,
  useEffect,
  useRef,
  useState,
  type ButtonHTMLAttributes,
  type ReactElement,
} from 'react'

interface DropdownItem {
  label: string
  onSelect: () => void
  variant?: 'default' | 'danger'
}

interface DropdownProps {
  trigger: ReactElement<ButtonHTMLAttributes<HTMLButtonElement>>
  items: DropdownItem[]
  align?: 'start' | 'end'
}

/**
 * Menu suspenso simples (fecha em clique fora ou Esc).
 *
 * Não implementa navegação por setas entre itens (padrão completo de menu
 * WAI-ARIA) — os itens são botões reais, então Tab already os alcança em
 * sequência; ver "melhorias futuras" no relatório da sprint.
 */
export function Dropdown({ trigger, items, align = 'end' }: DropdownProps) {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return undefined

    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false)
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [open])

  return (
    <div ref={containerRef} className="relative inline-block">
      {cloneElement(trigger, {
        onClick: () => {
          setOpen((current) => !current)
        },
        'aria-haspopup': 'menu',
        'aria-expanded': open,
      })}
      <AnimatePresence>
        {open && (
          <motion.div
            role="menu"
            initial={{ opacity: 0, y: -4, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.12 }}
            className={[
              'bg-surface-elevated border-border absolute z-50 mt-2 w-56 rounded-xl border p-1.5 shadow-2xl shadow-black/20 backdrop-blur-xl',
              align === 'end' ? 'right-0' : 'left-0',
            ].join(' ')}
          >
            {items.map((item) => (
              <button
                key={item.label}
                type="button"
                role="menuitem"
                onClick={() => {
                  setOpen(false)
                  item.onSelect()
                }}
                className={[
                  'flex w-full items-center rounded-lg px-3 py-2 text-left text-sm transition-colors',
                  item.variant === 'danger'
                    ? 'text-danger hover:bg-danger/10'
                    : 'text-content hover:bg-surface',
                ].join(' ')}
              >
                {item.label}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
