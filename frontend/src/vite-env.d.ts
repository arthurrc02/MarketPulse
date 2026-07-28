/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Opcional: quando ausente, `@/lib/env` aplica o fallback de desenvolvimento. */
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
