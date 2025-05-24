import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { AuthGuard } from './components/AuthGuard'
import { DarkModeProvider } from './contexts/DarkModeContext'
import Layout from './components/Layout'
import {
  Home,
  Login,
  Register,
  UserDashboard,
  AdminDashboard,
  SummaryView,
  TranscriptionView,
  NotFound
} from './pages'

export default function App() {
  return (
    <DarkModeProvider>
      <BrowserRouter>
        <AuthProvider>
          <Layout>
            <Routes>
              {/* Rotas públicas */}
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Rotas protegidas - Usuário comum */}
              <Route
                path="/user"
                element={
                  <AuthGuard>
                    <UserDashboard />
                  </AuthGuard>
                }
              />
              <Route
                path="/summaries/:videoId"
                element={
                  <AuthGuard>
                    <SummaryView />
                  </AuthGuard>
                }
              />
              <Route
                path="/transcriptions/:videoId"
                element={
                  <AuthGuard>
                    <TranscriptionView />
                  </AuthGuard>
                }
              />

              {/* Rotas protegidas - Admin */}
              <Route
                path="/admin"
                element={
                  <AuthGuard adminOnly>
                    <AdminDashboard />
                  </AuthGuard>
                }
              />

              {/* Rota 404 */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Layout>
        </AuthProvider>
      </BrowserRouter>
    </DarkModeProvider>
  )
}