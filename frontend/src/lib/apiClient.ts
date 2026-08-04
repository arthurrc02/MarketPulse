/**
 * Cliente HTTP fino sobre `fetch`.
 *
 * Anexa o access token automaticamente e, se uma resposta autenticada vier
 * 401, tenta uma única renovação silenciosa via refresh token antes de
 * desistir — assim uma sessão só expira de verdade quando o refresh também
 * falha (token revogado/expirado).
 */

import {
  clearTokens,
  getAccessToken,
  getStoredRefreshToken,
  setAccessToken,
  storeRefreshToken,
} from '@/lib/auth/tokenStore'
import { API_URL } from '@/lib/env'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

interface RequestOptions {
  method?: string
  body?: unknown
  /** Anexa o access token e habilita a renovação automática em 401. */
  authenticated?: boolean
}

interface RefreshResponseBody {
  access_token: string
  refresh_token: string
}

function isRefreshResponseBody(value: unknown): value is RefreshResponseBody {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as Record<string, unknown>).access_token === 'string' &&
    typeof (value as Record<string, unknown>).refresh_token === 'string'
  )
}

async function extractErrorMessage(response: Response): Promise<string> {
  let data: unknown
  try {
    data = await response.json()
  } catch {
    return 'Ocorreu um erro inesperado. Tente novamente.'
  }

  if (typeof data !== 'object' || data === null || !('detail' in data)) {
    return 'Ocorreu um erro inesperado. Tente novamente.'
  }

  const detail = data.detail
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    // Erro 422 de validação do Pydantic: uma lista de {loc, msg, type}.
    return detail
      .map((item: unknown) =>
        typeof item === 'object' && item !== null && 'msg' in item
          ? String(item.msg)
          : String(item),
      )
      .join(' ')
  }
  return 'Ocorreu um erro inesperado. Tente novamente.'
}

function buildRequestInit(options: RequestOptions): RequestInit {
  const isFormData = options.body instanceof FormData
  const headers = new Headers()
  // `FormData` nunca leva `Content-Type` explícito: o navegador define o
  // header sozinho, incluindo o `boundary` multipart — setá-lo à mão quebra
  // o parsing do multipart no servidor.
  if (!isFormData) {
    headers.set('Content-Type', 'application/json')
  }
  if (options.authenticated) {
    const token = getAccessToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }

  let body: BodyInit | null = null
  if (isFormData) {
    body = options.body as FormData
  } else if (options.body !== undefined) {
    body = JSON.stringify(options.body)
  }

  return {
    method: options.method ?? 'GET',
    headers,
    body,
  }
}

// Chamadas concorrentes que tomam 401 ao mesmo tempo compartilham a mesma
// tentativa de renovação, em vez de disparar um refresh cada uma.
let refreshInFlight: Promise<boolean> | null = null

function trySilentRefresh(): Promise<boolean> {
  refreshInFlight ??= (async () => {
    const storedRefreshToken = getStoredRefreshToken()
    if (!storedRefreshToken) return false

    try {
      const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: storedRefreshToken }),
      })
      if (!response.ok) return false

      const data: unknown = await response.json()
      if (!isRefreshResponseBody(data)) return false

      setAccessToken(data.access_token)
      storeRefreshToken(data.refresh_token)
      return true
    } catch {
      return false
    }
  })().finally(() => {
    refreshInFlight = null
  })

  return refreshInFlight
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const authenticated = options.authenticated ?? true

  let response = await fetch(`${API_URL}${path}`, buildRequestInit({ ...options, authenticated }))

  if (response.status === 401 && authenticated) {
    const refreshed = await trySilentRefresh()
    if (refreshed) {
      response = await fetch(`${API_URL}${path}`, buildRequestInit({ ...options, authenticated }))
    }
  }

  if (!response.ok) {
    if (response.status === 401) {
      clearTokens()
    }
    throw new ApiError(response.status, await extractErrorMessage(response))
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}
