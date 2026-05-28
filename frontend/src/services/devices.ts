import type { Device, DeviceCreate } from '../types/device'
import { apiRequest } from './api'

export function listDevices(): Promise<Device[]> {
  return apiRequest<Device[]>('/devices')
}

export function createDevice(data: DeviceCreate): Promise<Device> {
  return apiRequest<Device>('/devices', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
