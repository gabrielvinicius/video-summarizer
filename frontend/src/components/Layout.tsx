import { Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useDarkMode } from '../contexts/DarkModeContext'
import Navbar from './Navbar'
import Footer from './Footer'
import LoadingSpinner from './LoadingSpinner'

export default function Layout() {
  const { loading: authLoading } = useAuth()
  const { darkMode } = useDarkMode()

  if (authLoading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${darkMode ? 'dark bg-gray-900' : 'bg-white'}`}>
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className={`min-h-screen flex flex-col ${darkMode ? 'dark bg-gray-900' : 'bg-gray-50'}`}>
      <Navbar />
      <main className="flex-grow container mx-auto px-4 py-8">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}