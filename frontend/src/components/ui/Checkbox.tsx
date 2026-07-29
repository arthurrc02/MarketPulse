import { forwardRef, useId, type InputHTMLAttributes } from 'react'

import { CheckIcon } from '@/components/icons/Icons'

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string
  description?: string
}

/** Checkbox nativo (semântica e teclado de graça) com um visual customizado por cima. */
export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(function Checkbox(
  { label, description, id, className = '', ...props },
  ref,
) {
  const generatedId = useId()
  const inputId = id ?? generatedId

  return (
    <label htmlFor={inputId} className="flex cursor-pointer items-start gap-3 select-none">
      <span className="relative mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center">
        <input
          ref={ref}
          id={inputId}
          type="checkbox"
          className={['peer absolute inset-0 h-5 w-5 cursor-pointer opacity-0', className].join(
            ' ',
          )}
          {...props}
        />
        <span className="border-border bg-surface-elevated peer-checked:bg-primary peer-checked:border-primary peer-focus-visible:outline-primary pointer-events-none absolute inset-0 rounded-md border transition-colors peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2" />
        <CheckIcon className="text-primary-foreground pointer-events-none relative h-3.5 w-3.5 opacity-0 transition-opacity peer-checked:opacity-100" />
      </span>
      <span className="flex flex-col">
        <span className="text-content text-sm font-medium">{label}</span>
        {description && <span className="text-content-muted text-xs">{description}</span>}
      </span>
    </label>
  )
})
