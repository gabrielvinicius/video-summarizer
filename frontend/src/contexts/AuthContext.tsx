import { createContext, useContext, ReactNode, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import { toast } from 'react-toastify'

type User = {
  id: string
  email: string
  isAdmin?: boolean
}

type AuthContextType = {
  user: User | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  // Verifica autenticação ao carregar
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('token')
        if (token) {
          const response = await api.get('/auth/me')
          setUser({
            id: response.data.id,
            email: response.data.email,
            isAdmin: response.data.isAdmin
          })
        }
      } catch (error) {
        localStorage.removeItem('token')
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const response = await api.post('/auth/login', { email, password })
      localStorage.setItem('token', response.data.access_token)
      setUser({
        id: response.data.user_id,
        email: email
      })
      navigate('/user')
      toast.success('Login realizado com sucesso!')
    } catch (error) {
      toast.error('Credenciais inválidas')
      throw error
    }
  }

  const register = async (email: string, password: string) => {
    try {
      await api.post('/auth/register', { email, password })
      toast.success('Registro realizado! Faça login para continuar.')
      navigate('/login')
    } catch (error) {
      toast.error('Erro no registro')
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
    navigate('/login')
    toast.info('Sessão encerrada')
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        loading
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider')
  }
  return context
}