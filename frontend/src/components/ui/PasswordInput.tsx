import { forwardRef, useId, useState, type InputHTMLAttributes } from 'react'

import { EyeIcon, EyeOffIcon } from '@/components/icons/Icons'

type PasswordInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & {
  label: string
  error?: string
}

export const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(
  function PasswordInput({ label, error, id, className = '', ...props }, ref) {
    const [visible, setVisible] = useState(false)
    const generatedId = useId()
    const inputId = id ?? generatedId
    const errorId = `${inputId}-error`

    return (
      <div className="flex flex-col gap-1.5">
        <label htmlFor={inputId} className="text-content-muted text-sm font-medium">
          {label}
        </label>
        <div className="relative">
          <input
            ref={ref}
            id={inputId}
            type={visible ? 'text' : 'password'}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? errorId : undefined}
            className={[
              'bg-surface-elevated text-content placeholder:text-content-muted w-full rounded-xl border px-3.5 py-2.5 pr-11 text-sm placeholder:opacity-60',
              'outline-none transition-colors duration-150 focus:border-border-focus',
              error ? 'border-danger' : 'border-border',
              className,
            ].join(' ')}
            {...props}
          />
          <button
            type="button"
            onClick={() => {
              setVisible((current) => !current)
            }}
            className="text-content-muted hover:text-content absolute inset-y-0 right-0 flex items-center px-3"
            aria-label={visible ? 'Ocultar senha' : 'Mostrar senha'}
          >
            {visible ? <EyeOffIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
          </button>
        </div>
        {error && (
          <p id={errorId} role="alert" className="text-danger text-sm">
            {error}
          </p>
        )}
      </div>
    )
  },
)
