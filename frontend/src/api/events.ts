import type { Event } from '../types/event'
import { apiRequest, toQueryString } from './client'
import type { PaginatedResponse } from './types'
import { normalizePaginatedResponse } from './types'

export async function listEvents(params?: {
  page?: number
  limit?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}): Promise<PaginatedResponse<Event>> {
  const qs = toQueryString({
    page: params?.page ?? 1,
    limit: params?.limit ?? 50,
    sort_by: params?.sort_by ?? 'timestamp',
    sort_order: params?.sort_order ?? 'desc',
  })
  const raw = await apiRequest<PaginatedResponse<Event>>(`/events${qs}`)
  return normalizePaginatedResponse<Event>(raw)
}
