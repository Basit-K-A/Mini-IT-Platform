import type { Event } from '../types/event'
import { apiRequest, type PaginatedResponse } from './api'

export function listEvents(): Promise<Event[]> {
  return apiRequest<PaginatedResponse<Event>>('/events').then((res) => res.data)
}
