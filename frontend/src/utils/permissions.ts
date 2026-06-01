/**
 * Frontend permission helpers derived from the user's role.
 *
 * IMPORTANT: this only controls what the UI renders. The backend is the source of
 * truth and enforces every rule independently — hiding a button is never security.
 */

export type Role = 'viewer' | 'technician' | 'analyst' | 'admin' | string

export interface Permissions {
  canViewEvents: boolean
  canViewDevices: boolean
  canManageDevices: boolean
  canViewAudit: boolean
  canManageUsers: boolean
  canViewDashboard: boolean
}

export function getPermissions(role: Role | undefined | null): Permissions {
  const r = (role ?? '').toLowerCase()
  const isAdmin = r === 'admin'
  const isTechnician = r === 'technician'
  const isAnalyst = r === 'analyst'

  return {
    // Everyone authenticated can read events
    canViewEvents: true,
    // Devices: admin + technician only (viewers blocked, matches backend)
    canViewDevices: isAdmin || isTechnician,
    // Technicians may edit; create/delete are admin-only (enforced on backend)
    canManageDevices: isAdmin || isTechnician,
    // Audit trail: admin + analyst
    canViewAudit: isAdmin || isAnalyst,
    // User management: admin only
    canManageUsers: isAdmin,
    // Dashboard summary needs device visibility; analysts get a security view
    canViewDashboard: isAdmin || isTechnician || isAnalyst,
  }
}

/** Landing route for a role (viewers go straight to events). */
export function homeRouteForRole(role: Role | undefined | null): string {
  const perms = getPermissions(role)
  return perms.canViewDashboard ? '/dashboard' : '/events'
}
