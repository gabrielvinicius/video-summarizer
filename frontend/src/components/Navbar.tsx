import { Link } from 'react-router-dom'
import { useAuth, useDarkMode } from '../contexts'
import DarkModeToggle from './DarkModeToggle'

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth()
  const { darkMode } = useDarkMode()

  return (
    <header className={`shadow-sm ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
      <nav className="container mx-auto px-4 py-3 flex justify-between items-center">
        <Link to="/" className="text-xl font-bold">
          VideoSummarizer
        </Link>

        <div className="flex items-center gap-4">
          <DarkModeToggle />

          {isAuthenticated ? (
            <>
              <Link to={user?.isAdmin ? '/admin' : '/user'} className="hover:underline">
                Dashboard
              </Link>
              <button onClick={logout} className="text-red-500 hover:underline">
                Sair
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="hover:underline">
                Login
              </Link>
              <Link to="/register" className="hover:underline">
                Registrar
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  )
}