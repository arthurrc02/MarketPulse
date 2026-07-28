import { forwardRef, useId, useState, type InputHTMLAttributes } from 'react'

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

function EyeIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <path
        d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}

function EyeOffIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <path
        d="M3 3l18 18M10.6 10.6a3 3 0 0 0 4.24 4.24M9.4 5.5A10.4 10.4 0 0 1 12 5c6.5 0 10 7 10 7a13.6 13.6 0 0 1-3.1 3.9M6.6 6.6C4.3 8.1 2 12 2 12a13.6 13.6 0 0 0 5.1 5.4"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  )
}
