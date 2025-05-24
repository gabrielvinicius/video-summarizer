import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import AuthFormContainer from '../components/AuthFormContainer'
import InputField from '../components/InputField'
import Button from '../components/Button'
import { toast } from 'react-toastify'

export default function Register() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (password !== confirmPassword) {
      toast.error('As senhas não coincidem')
      return
    }

    setLoading(true)
    try {
      await register(email, password)
      toast.success('Registro realizado com sucesso! Faça login para continuar.')
      navigate('/login')
    } catch (error) {
      toast.error('Falha no registro. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthFormContainer title="Criar Conta">
      <form onSubmit={handleSubmit} className="space-y-6">
        <InputField
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoFocus
        />

        <InputField
          label="Senha"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={6}
        />

        <InputField
          label="Confirmar Senha"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />

        <Button type="submit" disabled={loading} fullWidth>
          {loading ? 'Registrando...' : 'Registrar'}
        </Button>
      </form>

      <div className="mt-6 text-center text-sm text-gray-500">
        <p>
          Já tem uma conta?{' '}
          <Link
            to="/login"
            className="font-medium text-blue-600 hover:text-blue-500"
          >
            Faça login
          </Link>
        </p>
      </div>
    </AuthFormContainer>
  )
}