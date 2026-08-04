import { motion } from 'framer-motion'
import { useId, useRef, useState, type DragEvent } from 'react'

import { UploadsIcon } from '@/components/icons/Icons'

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void
  accept?: string
  multiple?: boolean
  disabled?: boolean
  hint?: string
}

/**
 * Área de arrastar-e-soltar (drag & drop) com seleção manual por clique.
 *
 * É um `<button>` real (não uma `<div>` com `role="button"`) — dá foco,
 * `Enter`/`Espaço` e leitor de tela de graça, sem reimplementar semântica de
 * botão manualmente. Os handlers de drag funcionam em qualquer elemento.
 *
 * O `<input type="file">` fica **fora** do `<button>`, como irmão oculto: um
 * `<button>` não permite conteúdo interativo aninhado (a spec do HTML proíbe
 * `<input>` dentro de `<button>`) — o próprio botão é o único elemento
 * alcançável por teclado/leitor de tela; o input só é acionado
 * programaticamente.
 */
export function FileUpload({
  onFilesSelected,
  accept = '.csv,.xlsx',
  multiple = true,
  disabled = false,
  hint = 'Arquivos CSV ou XLSX',
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const inputId = useId()

  function handleDragEnter(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault()
    if (!disabled) setIsDragging(true)
  }

  function handleDragOver(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault()
  }

  function handleDragLeave(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault()
    if (event.currentTarget.contains(event.relatedTarget as Node)) return
    setIsDragging(false)
  }

  function handleDrop(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault()
    setIsDragging(false)
    if (disabled) return
    const files = Array.from(event.dataTransfer.files)
    if (files.length > 0) onFilesSelected(files)
  }

  return (
    <div className="relative">
      <button
        type="button"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        aria-describedby={`${inputId}-hint`}
        className={[
          'border-border bg-surface-elevated/50 flex w-full flex-col items-center gap-3 rounded-2xl border-2 border-dashed px-6 py-12 text-center transition-colors duration-150',
          'focus-visible:outline-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
          'disabled:cursor-not-allowed disabled:opacity-60',
          isDragging ? 'border-primary bg-primary/5' : 'hover:border-border-focus',
        ].join(' ')}
      >
        <motion.span
          animate={{ scale: isDragging ? 1.1 : 1 }}
          transition={{ duration: 0.15 }}
          className={isDragging ? 'text-primary' : 'text-content-muted'}
        >
          <UploadsIcon className="h-8 w-8" />
        </motion.span>
        <span className="text-content text-sm font-medium">
          {isDragging ? 'Solte para enviar' : 'Arraste arquivos aqui ou clique para selecionar'}
        </span>
        <span id={`${inputId}-hint`} className="text-content-muted text-xs">
          {hint}
        </span>
      </button>
      <input
        ref={inputRef}
        id={inputId}
        type="file"
        accept={accept}
        multiple={multiple}
        disabled={disabled}
        tabIndex={-1}
        aria-hidden="true"
        className="sr-only"
        onChange={(event) => {
          const files = Array.from(event.target.files ?? [])
          if (files.length > 0) onFilesSelected(files)
          // Permite selecionar o mesmo arquivo de novo em seguida (o browser
          // não dispara `onChange` se o `value` não mudar).
          event.target.value = ''
        }}
      />
    </div>
  )
}
