import { ReactNode } from 'react'
import { useDarkMode } from '../contexts/DarkModeContext'
import Logo from './Logo'

type AuthFormContainerProps = {
  title: string
  children: ReactNode
}

export default function AuthFormContainer({ title, children }: AuthFormContainerProps) {
  const { darkMode } = useDarkMode()

  return (
    <div className={`min-h-screen flex items-center justify-center ${darkMode ? 'dark bg-gray-900' : 'bg-gray-50'}`}>
      <div className="w-full max-w-md px-8 py-12 space-y-8 bg-white dark:bg-gray-800 rounded-lg shadow-md">
        <div className="flex justify-center">
          <Logo className="h-16 w-auto" />
        </div>
        <h2 className="text-3xl font-extrabold text-center text-gray-900 dark:text-white">
          {title}
        </h2>
        {children}
      </div>
    </div>
  )
}