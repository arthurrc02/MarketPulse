import { forwardRef, useId, type InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, id, className = '', ...props },
  ref,
) {
  const generatedId = useId()
  const inputId = id ?? generatedId
  const errorId = `${inputId}-error`

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-content-muted text-sm font-medium">
        {label}
      </label>
      <input
        ref={ref}
        id={inputId}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
        className={[
          'bg-surface-elevated text-content placeholder:text-content-muted rounded-xl border px-3.5 py-2.5 text-sm placeholder:opacity-60',
          'outline-none transition-colors duration-150 focus:border-border-focus',
          error ? 'border-danger' : 'border-border',
          className,
        ].join(' ')}
        {...props}
      />
      {error && (
        <p id={errorId} role="alert" className="text-danger text-sm">
          {error}
        </p>
      )}
    </div>
  )
})
