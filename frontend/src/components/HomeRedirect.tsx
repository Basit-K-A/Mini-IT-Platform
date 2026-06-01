import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

/** Sends each role to its appropriate landing page (viewers -> events). */
export function HomeRedirect() {
  const { homeRoute } = useAuth()
  return <Navigate to={homeRoute} replace />
}
