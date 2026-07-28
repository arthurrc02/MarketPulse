/**
 * Guarda os tokens de sessão fora da árvore do React.
 *
 * O access token vive só em memória — nunca é persistido — para reduzir a
 * janela de exposição a um roubo via XSS. O refresh token precisa sobreviver
 * a um reload de página (é o que torna "permanecer autenticado" possível) e
 * fica em `localStorage`; o bootstrap da sessão (`AuthProvider`) o troca por
 * um access token novo a cada carregamento da aplicação.
 */

const REFRESH_TOKEN_KEY = 'marketpulse.refresh_token'

let accessToken: string | null = null

export function getAccessToken(): string | null {
  return accessToken
}

export function setAccessToken(token: string | null): void {
  accessToken = token
}

export function getStoredRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function storeRefreshToken(token: string): void {
  localStorage.setItem(REFRESH_TOKEN_KEY, token)
}

export function clearTokens(): void {
  accessToken = null
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}
