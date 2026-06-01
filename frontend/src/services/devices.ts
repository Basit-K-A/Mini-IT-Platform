import type { Device, DeviceCreate } from '../types/device'
import { apiRequest, type PaginatedResponse } from './api'

export function listDevices(params?: { page?: number; limit?: number }): Promise<Device[]> {
  const search = new URLSearchParams()
  if (params?.page) search.set('page', String(params.page))
  if (params?.limit) search.set('limit', String(params.limit))
  const qs = search.toString()
  const path = qs ? `/devices?${qs}` : '/devices'
  return apiRequest<PaginatedResponse<Device>>(path).then((res) => res.data)
}

export function createDevice(data: DeviceCreate): Promise<Device> {
  return apiRequest<Device>('/devices', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
