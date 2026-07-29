import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react'

import { Spinner } from '@/components/ui/Spinner'

type IconButtonVariant = 'primary' | 'secondary' | 'ghost'

// `aria-label` é obrigatório: um botão só de ícone sem nome acessível é um
// dos erros de acessibilidade mais comuns em Design Systems próprios.
interface IconButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'aria-label'> {
  icon: ReactNode
  'aria-label': string
  variant?: IconButtonVariant
  isLoading?: boolean
}

const VARIANT_CLASSES: Record<IconButtonVariant, string> = {
  primary:
    'bg-primary text-primary-foreground hover:bg-primary-hover focus-visible:outline-primary',
  secondary:
    'bg-surface-elevated text-content border border-border hover:border-border-focus focus-visible:outline-primary',
  ghost:
    'bg-transparent text-content-muted hover:bg-surface-elevated hover:text-content focus-visible:outline-primary',
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  { icon, variant = 'ghost', isLoading = false, disabled, className = '', ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      disabled={disabled ?? isLoading}
      className={[
        'inline-flex h-9 w-9 items-center justify-center rounded-xl',
        'transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
        'disabled:cursor-not-allowed disabled:opacity-60',
        VARIANT_CLASSES[variant],
        className,
      ].join(' ')}
      {...props}
    >
      {isLoading ? <Spinner className="h-4 w-4" /> : icon}
    </button>
  )
})
