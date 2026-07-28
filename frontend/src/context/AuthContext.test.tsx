import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '@/context/AuthContext'
import { useAuth } from '@/hooks/useAuth'
import * as authApi from '@/lib/auth/api'

vi.mock('@/lib/auth/api')

const mockedAuthApi = vi.mocked(authApi)

const REFRESH_TOKEN_KEY = 'marketpulse.refresh_token'

const SAMPLE_USER = {
  id: '1',
  email: 'user@example.com',
  isActive: true,
  createdAt: '2026-01-01T00:00:00Z',
}

const SAMPLE_TOKENS = {
  accessToken: 'access-token',
  refreshToken: 'refresh-token',
  tokenType: 'bearer',
  expiresIn: 900,
}

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>
}

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('starts unauthenticated when there is no stored refresh token', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.status).toBe('unauthenticated')
    })
    expect(mockedAuthApi.refreshTokens).not.toHaveBeenCalled()
  })

  it('hydrates the session from a stored refresh token', async () => {
    localStorage.setItem(REFRESH_TOKEN_KEY, 'stored-refresh-token')
    mockedAuthApi.refreshTokens.mockResolvedValue({
      ...SAMPLE_TOKENS,
      refreshToken: 'rotated-refresh-token',
    })
    mockedAuthApi.getCurrentUser.mockResolvedValue(SAMPLE_USER)

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.status).toBe('authenticated')
    })
    expect(result.current.user?.email).toBe('user@example.com')
    expect(mockedAuthApi.refreshTokens).toHaveBeenCalledWith('stored-refresh-token')
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBe('rotated-refresh-token')
  })

  it('clears the session when the stored refresh token is rejected', async () => {
    localStorage.setItem(REFRESH_TOKEN_KEY, 'expired-token')
    mockedAuthApi.refreshTokens.mockRejectedValue(new Error('token expired'))

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.status).toBe('unauthenticated')
    })
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull()
  })

  it('login authenticates the user and stores the tokens', async () => {
    mockedAuthApi.loginUser.mockResolvedValue(SAMPLE_TOKENS)
    mockedAuthApi.getCurrentUser.mockResolvedValue(SAMPLE_USER)

    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => {
      expect(result.current.status).toBe('unauthenticated')
    })

    await act(async () => {
      await result.current.login({ email: 'user@example.com', password: 'Sup3rSecret!' })
    })

    expect(result.current.status).toBe('authenticated')
    expect(result.current.user?.email).toBe('user@example.com')
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBe('refresh-token')
  })

  it('register creates the account and then logs in with the same credentials', async () => {
    mockedAuthApi.registerUser.mockResolvedValue(SAMPLE_USER)
    mockedAuthApi.loginUser.mockResolvedValue(SAMPLE_TOKENS)
    mockedAuthApi.getCurrentUser.mockResolvedValue(SAMPLE_USER)

    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => {
      expect(result.current.status).toBe('unauthenticated')
    })

    await act(async () => {
      await result.current.register({ email: 'user@example.com', password: 'Sup3rSecret!' })
    })

    expect(mockedAuthApi.registerUser).toHaveBeenCalledWith({
      email: 'user@example.com',
      password: 'Sup3rSecret!',
    })
    expect(mockedAuthApi.loginUser).toHaveBeenCalledWith({
      email: 'user@example.com',
      password: 'Sup3rSecret!',
    })
    expect(result.current.status).toBe('authenticated')
  })

  it('logout clears the session even if the API call fails', async () => {
    mockedAuthApi.loginUser.mockResolvedValue(SAMPLE_TOKENS)
    mockedAuthApi.getCurrentUser.mockResolvedValue(SAMPLE_USER)
    mockedAuthApi.logoutUser.mockRejectedValue(new Error('network error'))

    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => {
      expect(result.current.status).toBe('unauthenticated')
    })

    await act(async () => {
      await result.current.login({ email: 'user@example.com', password: 'Sup3rSecret!' })
    })
    expect(result.current.status).toBe('authenticated')

    await act(async () => {
      await result.current.logout()
    })

    expect(result.current.status).toBe('unauthenticated')
    expect(result.current.user).toBeNull()
    expect(mockedAuthApi.logoutUser).toHaveBeenCalledWith('refresh-token')
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull()
  })
})
