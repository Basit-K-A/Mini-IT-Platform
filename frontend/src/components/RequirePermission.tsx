import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import type { Permissions } from '../utils/permissions'
import { LoadingSpinner } from './LoadingSpinner'

/**
 * Route guard that allows access only when the user has a given permission.
 * Unauthorized users are redirected to their role-appropriate home route.
 *
 * Frontend-only convenience — the backend independently enforces every rule.
 */
export function RequirePermission({ permission }: { permission: keyof Permissions }) {
  const { loading, permissions, homeRoute } = useAuth()

  if (loading) {
    return (
      <div className="page-center">
        <LoadingSpinner label="Checking permissions…" />
      </div>
    )
  }

  if (!permissions[permission]) {
    return <Navigate to={homeRoute} replace />
  }

  return <Outlet />
}
