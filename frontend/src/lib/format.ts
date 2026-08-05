const SIZE_UNITS = ['B', 'KB', 'MB', 'GB'] as const

/** Formata bytes de forma legível (`"1.2 MB"`, `"340 KB"`). */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${String(bytes)} B`

  let value = bytes
  let unitIndex = 0
  while (value >= 1024 && unitIndex < SIZE_UNITS.length - 1) {
    value /= 1024
    unitIndex += 1
  }

  // `unitIndex` nunca sai de [0, SIZE_UNITS.length - 1] pelo laço acima, mas
  // `noUncheckedIndexedAccess` não sabe disso — o fallback é só para o TS.
  const unit = SIZE_UNITS[unitIndex] ?? 'B'
  const precision = value < 10 && unitIndex > 0 ? 1 : 0
  return `${value.toFixed(precision)} ${unit}`
}

/** Formata uma data ISO no padrão `dd/mm/aaaa hh:mm`. */
export function formatDateTime(isoDate: string): string {
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(isoDate))
}

/** Formata a duração entre duas datas ISO (`"2,3s"`, `"1min 04s"`). */
export function formatDuration(startIsoDate: string, endIsoDate: string): string {
  const totalSeconds = (new Date(endIsoDate).getTime() - new Date(startIsoDate).getTime()) / 1000
  if (totalSeconds < 60) {
    return `${totalSeconds.toFixed(1).replace('.', ',')}s`
  }
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = Math.round(totalSeconds % 60)
  return `${String(minutes)}min ${String(seconds).padStart(2, '0')}s`
}
