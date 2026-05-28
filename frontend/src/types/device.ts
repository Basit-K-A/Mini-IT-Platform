export interface Device {
  id: number
  hostname: string
  ip_address: string
  operating_system: string
  status: string
  owner_id: number
}

export interface DeviceCreate {
  hostname: string
  ip_address: string
  operating_system: string
  status: string
  owner_id: number
}
