import type { AuditLog } from '../types/audit'
import { apiRequest, toQueryString } from './client'
import type { AuditListQuery, PaginatedResponse } from './types'
import { normalizePaginatedResponse } from './types'

export async function listAuditLogs(
  query: AuditListQuery = {},
): Promise<PaginatedResponse<AuditLog>> {
  const qs = toQueryString({
    page: query.page,
    limit: query.limit,
    sort_by: query.sort_by,
    sort_order: query.sort_order,
    action: query.action,
    user_id: query.user_id,
    ip_address: query.ip_address,
  })
  const raw = await apiRequest<PaginatedResponse<AuditLog>>(`/audit-logs${qs}`)
  return normalizePaginatedResponse<AuditLog>(raw)
}
