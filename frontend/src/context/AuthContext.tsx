import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { AuthContext, type AuthStatus } from '@/context/authContextDefinition'
import * as authApi from '@/lib/auth/api'
import type { AuthUser, Credentials } from '@/lib/auth/api'
import {
  clearTokens,
  getStoredRefreshToken,
  setAccessToken,
  storeRefreshToken,
} from '@/lib/auth/tokenStore'

/**
 * Troca o refresh token salvo por uma sessão nova ao carregar a aplicação.
 *
 * É o que faz "permanecer autenticado" funcionar entre reloads: o access
 * token nunca é persistido (ver `lib/auth/tokenStore`), então cada
 * carregamento precisa renová-lo a partir do refresh token em `localStorage`.
 */
async function hydrateFromStoredRefreshToken(): Promise<AuthUser | null> {
  const storedRefreshToken = getStoredRefreshToken()
  if (!storedRefreshToken) return null

  const tokens = await authApi.refreshTokens(storedRefreshToken)
  setAccessToken(tokens.accessToken)
  storeRefreshToken(tokens.refreshToken)
  return authApi.getCurrentUser()
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [status, setStatus] = useState<AuthStatus>('loading')

  useEffect(() => {
    let isMounted = true

    hydrateFromStoredRefreshToken()
      .then((hydratedUser) => {
        if (!isMounted) return
        setUser(hydratedUser)
        setStatus(hydratedUser ? 'authenticated' : 'unauthenticated')
      })
      .catch(() => {
        if (!isMounted) return
        clearTokens()
        setUser(null)
        setStatus('unauthenticated')
      })

    return () => {
      isMounted = false
    }
  }, [])

  const login = useCallback(async (credentials: Credentials) => {
    const tokens = await authApi.loginUser(credentials)
    setAccessToken(tokens.accessToken)
    storeRefreshToken(tokens.refreshToken)
    const authenticatedUser = await authApi.getCurrentUser()
    setUser(authenticatedUser)
    setStatus('authenticated')
  }, [])

  const register = useCallback(
    async (credentials: Credentials) => {
      await authApi.registerUser(credentials)
      // O cadastro não retorna tokens (ver docs/api.md) — login imediatamente
      // após para uma experiência de onboarding contínua.
      await login(credentials)
    },
    [login],
  )

  const logout = useCallback(async () => {
    const storedRefreshToken = getStoredRefreshToken()
    if (storedRefreshToken) {
      try {
        await authApi.logoutUser(storedRefreshToken)
      } catch {
        // A sessão local é encerrada mesmo se a chamada falhar (rede
        // indisponível, token já expirado) — o objetivo final já é atingido.
      }
    }
    clearTokens()
    setUser(null)
    setStatus('unauthenticated')
  }, [])

  const value = useMemo(
    () => ({ user, status, login, register, logout }),
    [user, status, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
