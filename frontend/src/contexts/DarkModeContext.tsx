import { createContext, useContext, ReactNode, useState, useEffect } from 'react'

type DarkModeContextType = {
  darkMode: boolean
  toggleDarkMode: () => void
}

const DarkModeContext = createContext<DarkModeContextType | undefined>(undefined)

export function DarkModeProvider({ children }: { children: ReactNode }) {
  const [darkMode, setDarkMode] = useState(() => {
    // Verifica preferência salva ou do sistema
    const savedMode = localStorage.getItem('darkMode')
    if (savedMode !== null) return savedMode === 'true'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  // Aplica as classes no HTML e salva preferência
  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
    localStorage.setItem('darkMode', String(darkMode))
  }, [darkMode])

  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
  }

  return (
    <DarkModeContext.Provider value={{ darkMode, toggleDarkMode }}>
      {children}
    </DarkModeContext.Provider>
  )
}

export const useDarkMode = () => {
  const context = useContext(DarkModeContext)
  if (!context) {
    throw new Error('useDarkMode deve ser usado dentro de DarkModeProvider')
  }
  return context
}