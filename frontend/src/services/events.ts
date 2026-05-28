import type { Event } from '../types/event'
import { apiRequest } from './api'

export function listEvents(): Promise<Event[]> {
  return apiRequest<Event[]>('/events')
}
