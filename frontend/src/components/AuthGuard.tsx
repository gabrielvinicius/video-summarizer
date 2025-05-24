import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import LoadingSpinner from './LoadingSpinner'

type AuthGuardProps = {
  children: React.ReactNode
  adminOnly?: boolean
}

export default function AuthGuard({ children, adminOnly = false }: AuthGuardProps) {
  const { user, isAuthenticated, loading } = useAuth()

  if (loading) {
    return <LoadingSpinner size="md" />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (adminOnly && !user?.isAdmin) {
    return <Navigate to="/user" replace />
  }

  return <>{children}</>
}