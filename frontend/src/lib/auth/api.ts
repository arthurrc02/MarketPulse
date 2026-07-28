/**
 * Chamadas HTTP de autenticação, tipadas em camelCase para o resto da app.
 *
 * O backend responde em snake_case (convenção Python); os `map*` abaixo são
 * o único lugar onde esse formato de wire aparece.
 */

import { apiRequest } from '@/lib/apiClient'

export interface AuthUser {
  id: string
  email: string
  isActive: boolean
  createdAt: string
}

export interface TokenPair {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
}

export interface Credentials {
  email: string
  password: string
}

interface UserResponseBody {
  id: string
  email: string
  is_active: boolean
  created_at: string
}

interface TokenResponseBody {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

function mapUser(body: UserResponseBody): AuthUser {
  return { id: body.id, email: body.email, isActive: body.is_active, createdAt: body.created_at }
}

function mapTokens(body: TokenResponseBody): TokenPair {
  return {
    accessToken: body.access_token,
    refreshToken: body.refresh_token,
    tokenType: body.token_type,
    expiresIn: body.expires_in,
  }
}

export async function registerUser(credentials: Credentials): Promise<AuthUser> {
  const body = await apiRequest<UserResponseBody>('/api/v1/auth/register', {
    method: 'POST',
    body: credentials,
    authenticated: false,
  })
  return mapUser(body)
}

export async function loginUser(credentials: Credentials): Promise<TokenPair> {
  const body = await apiRequest<TokenResponseBody>('/api/v1/auth/login', {
    method: 'POST',
    body: credentials,
    authenticated: false,
  })
  return mapTokens(body)
}

export async function refreshTokens(refreshToken: string): Promise<TokenPair> {
  const body = await apiRequest<TokenResponseBody>('/api/v1/auth/refresh', {
    method: 'POST',
    body: { refresh_token: refreshToken },
    authenticated: false,
  })
  return mapTokens(body)
}

export async function logoutUser(refreshToken: string): Promise<void> {
  await apiRequest('/api/v1/auth/logout', {
    method: 'POST',
    body: { refresh_token: refreshToken },
    authenticated: false,
  })
}

export async function getCurrentUser(): Promise<AuthUser> {
  const body = await apiRequest<UserResponseBody>('/api/v1/users/me', { authenticated: true })
  return mapUser(body)
}
