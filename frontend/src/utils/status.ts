const ONLINE_STATUSES = new Set(['active', 'online', 'up', 'running'])

export function isOnlineStatus(status: string): boolean {
  return ONLINE_STATUSES.has(status.toLowerCase())
}

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'neutral'

export function deviceStatusVariant(status: string): BadgeVariant {
  if (isOnlineStatus(status)) return 'success'
  if (['maintenance', 'degraded', 'warning'].includes(status.toLowerCase())) return 'warning'
  if (['offline', 'down', 'inactive', 'error'].includes(status.toLowerCase())) return 'danger'
  return 'neutral'
}

export function severityVariant(severity: string): BadgeVariant {
  const s = severity.toLowerCase()
  if (s === 'critical' || s === 'high') return 'danger'
  if (s === 'medium' || s === 'warning') return 'warning'
  if (s === 'low' || s === 'info') return 'success'
  return 'neutral'
}
