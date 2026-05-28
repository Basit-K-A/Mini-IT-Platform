import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider } from './hooks/useAuth'
import { DashboardLayout } from './layouts/DashboardLayout'
import { DashboardPage } from './pages/Dashboard'
import { DevicesPage } from './pages/Devices'
import { EventsPage } from './pages/Events'
import { LoginPage } from './pages/Login'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="devices" element={<DevicesPage />} />
              <Route path="events" element={<EventsPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
