import { forwardRef, useId, type SelectHTMLAttributes } from 'react'

import { ChevronDownIcon } from '@/components/icons/Icons'

interface SelectOption {
  value: string
  label: string
}

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'children'> {
  label: string
  options: SelectOption[]
  error?: string
  placeholder?: string
}

/**
 * `<select>` nativo estilizado, em vez de um listbox customizado.
 *
 * Um listbox próprio (popup + roving tabindex + typeahead) tem mais
 * superfície de falha de acessibilidade do que o controle nativo do
 * navegador, que já resolve teclado, leitor de tela e mobile de graça — a
 * troca de controle visual sobre as `<option>` não compensa o risco aqui.
 */
export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { label, options, error, placeholder, id, className = '', defaultValue, ...props },
  ref,
) {
  const generatedId = useId()
  const selectId = id ?? generatedId
  const errorId = `${selectId}-error`

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={selectId} className="text-content-muted text-sm font-medium">
        {label}
      </label>
      <div className="relative">
        <select
          ref={ref}
          id={selectId}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
          defaultValue={defaultValue ?? (placeholder ? '' : undefined)}
          className={[
            'bg-surface-elevated text-content w-full appearance-none rounded-xl border px-3.5 py-2.5 pr-10 text-sm',
            'outline-none transition-colors duration-150 focus:border-border-focus disabled:cursor-not-allowed disabled:opacity-60',
            error ? 'border-danger' : 'border-border',
            className,
          ].join(' ')}
          {...props}
        >
          {placeholder && (
            <option value="" disabled hidden>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDownIcon className="text-content-muted pointer-events-none absolute top-1/2 right-3.5 h-4 w-4 -translate-y-1/2" />
      </div>
      {error && (
        <p id={errorId} role="alert" className="text-danger text-sm">
          {error}
        </p>
      )}
    </div>
  )
})
