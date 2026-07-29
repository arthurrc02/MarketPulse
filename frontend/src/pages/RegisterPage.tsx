import { useState, type SubmitEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { AuthLayout } from '@/components/layout/AuthLayout'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { PasswordInput } from '@/components/ui/PasswordInput'
import { useAuth } from '@/hooks/useAuth'
import { useToast } from '@/hooks/useToast'
import { ApiError } from '@/lib/apiClient'

export function RegisterPage() {
  const { register } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    setError(null)

    if (password !== confirmPassword) {
      setError('As senhas não coincidem.')
      return
    }

    setIsSubmitting(true)
    try {
      await register({ email, password })
      showToast({ variant: 'success', message: 'Conta criada com sucesso!' })
      void navigate('/app', { replace: true })
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Não foi possível criar sua conta. Tente novamente.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthLayout
      title="Criar conta no MarketPulse"
      subtitle="Comece a organizar os relatórios dos seus marketplaces."
      footer={
        <>
          Já tem uma conta?{' '}
          <Link to="/login" className="text-primary font-medium hover:underline">
            Entrar
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
          autoComplete="new-password"
          required
          minLength={8}
          value={password}
          onChange={(event) => {
            setPassword(event.target.value)
          }}
        />
        <PasswordInput
          label="Confirmar senha"
          autoComplete="new-password"
          required
          value={confirmPassword}
          onChange={(event) => {
            setConfirmPassword(event.target.value)
          }}
        />
        {error && (
          <p role="alert" className="text-danger text-sm">
            {error}
          </p>
        )}
        <Button type="submit" fullWidth isLoading={isSubmitting}>
          Criar conta
        </Button>
      </form>
    </AuthLayout>
  )
}
