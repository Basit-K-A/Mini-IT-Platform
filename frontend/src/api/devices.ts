import type { Device, DeviceCreate, DeviceUpdate } from '../types/device'
import { apiRequest, toQueryString } from './client'
import type { DeviceListQuery, PaginatedResponse } from './types'
import { normalizePaginatedResponse } from './types'

export async function listDevices(
  query: DeviceListQuery = {},
): Promise<PaginatedResponse<Device>> {
  const qs = toQueryString({
    page: query.page,
    limit: query.limit,
    sort_by: query.sort_by,
    sort_order: query.sort_order,
    status: query.status,
    department: query.department,
    owner_id: query.owner_id,
    assigned_to: query.assigned_to,
    hostname: query.hostname,
    operating_system: query.operating_system,
  })
  const raw = await apiRequest<PaginatedResponse<Device>>(`/devices${qs}`)
  return normalizePaginatedResponse<Device>(raw)
}

export function createDevice(data: DeviceCreate): Promise<Device> {
  return apiRequest<Device>('/devices', { method: 'POST', body: data })
}

export function updateDevice(id: number, data: DeviceUpdate): Promise<Device> {
  return apiRequest<Device>(`/devices/${id}`, { method: 'PUT', body: data })
}

export function deleteDevice(id: number): Promise<void> {
  return apiRequest<void>(`/devices/${id}`, { method: 'DELETE' })
}
