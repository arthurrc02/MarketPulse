import { AnimatePresence, motion } from 'framer-motion'
import { cloneElement, useId, useState, type HTMLAttributes, type ReactElement } from 'react'

interface TooltipProps {
  content: string
  children: ReactElement<HTMLAttributes<HTMLElement>>
  side?: 'top' | 'bottom'
}

/**
 * Tooltip com posicionamento fixo (sempre acima ou abaixo do gatilho).
 *
 * Sem detecção de colisão com a borda da viewport nem flip automático — isso
 * exigiria uma lib de posicionamento (Floating UI) que o projeto
 * deliberadamente evita nesta sprint (ver decisions.md). Para os usos atuais
 * (ícones de contexto em cards e na barra superior), a limitação não afeta a
 * legibilidade.
 */
export function Tooltip({ content, children, side = 'top' }: TooltipProps) {
  const [visible, setVisible] = useState(false)
  const tooltipId = useId()

  const show = () => {
    setVisible(true)
  }
  const hide = () => {
    setVisible(false)
  }

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {cloneElement(children, { 'aria-describedby': tooltipId })}
      <AnimatePresence>
        {visible && (
          <motion.span
            id={tooltipId}
            role="tooltip"
            initial={{ opacity: 0, y: side === 'top' ? 4 : -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.12 }}
            className={[
              'bg-surface-elevated border-border text-content pointer-events-none absolute z-50 w-max max-w-xs rounded-lg border px-2.5 py-1.5 text-xs shadow-lg',
              side === 'top'
                ? 'bottom-full left-1/2 mb-2 -translate-x-1/2'
                : 'top-full left-1/2 mt-2 -translate-x-1/2',
            ].join(' ')}
          >
            {content}
          </motion.span>
        )}
      </AnimatePresence>
    </span>
  )
}
