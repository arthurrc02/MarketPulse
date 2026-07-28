import { useState, type SubmitEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { AuthLayout } from '@/components/layout/AuthLayout'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { PasswordInput } from '@/components/ui/PasswordInput'
import { useAuth } from '@/hooks/useAuth'
import { ApiError } from '@/lib/apiClient'

interface LocationState {
  from?: { pathname: string }
}

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await login({ email, password })
      const state = location.state as LocationState | null
      void navigate(state?.from?.pathname ?? '/app', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível entrar. Tente novamente.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthLayout
      title="Entrar no MarketPulse"
      subtitle="Acesse sua conta para continuar."
      footer={
        <>
          Ainda não tem uma conta?{' '}
          <Link to="/register" className="text-primary font-medium hover:underline">
            Cadastre-se
          </Link>
        </>
      }
    >
      <form
        onSubmit={(event) => void handleSubmit(event)}
        className="flex flex-col gap-4"
        noValidate
      >
        <Input
          label="E-mail"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => {
            setEmail(event.target.value)
          }}
        />
        <PasswordInput
          label="Senha"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => {
            setPassword(event.target.value)
          }}
        />
        {error && (
          <p role="alert" className="text-danger text-sm">
            {error}
          </p>
        )}
        <Button type="submit" fullWidth isLoading={isSubmitting}>
          Entrar
        </Button>
      </form>
    </AuthLayout>
  )
}
