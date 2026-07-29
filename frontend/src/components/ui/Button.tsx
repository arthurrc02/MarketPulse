import { forwardRef, type ButtonHTMLAttributes } from 'react'

import { Spinner } from '@/components/ui/Spinner'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  isLoading?: boolean
  fullWidth?: boolean
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    'bg-primary text-primary-foreground hover:bg-primary-hover focus-visible:outline-primary',
  secondary:
    'bg-surface-elevated text-content border border-border hover:border-border-focus focus-visible:outline-primary',
  ghost: 'bg-transparent text-content-muted hover:text-content focus-visible:outline-primary',
  danger: 'bg-danger text-danger-foreground hover:bg-danger-hover focus-visible:outline-danger',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    variant = 'primary',
    isLoading = false,
    fullWidth = false,
    disabled,
    className = '',
    children,
    ...props
  },
  ref,
) {
  return (
    <button
      ref={ref}
      disabled={disabled ?? isLoading}
      className={[
        'inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium',
        'transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
        'disabled:cursor-not-allowed disabled:opacity-60',
        fullWidth ? 'w-full' : '',
        VARIANT_CLASSES[variant],
        className,
      ].join(' ')}
      {...props}
    >
      {isLoading && <Spinner className="h-4 w-4" />}
      {children}
    </button>
  )
})
