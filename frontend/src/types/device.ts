export interface Device {
  id: number
  hostname: string
  ip_address: string
  operating_system: string
  status: string
  department?: string | null
  owner_id: number
  created_at?: string | null
}

export interface DeviceCreate {
  hostname: string
  ip_address: string
  operating_system: string
  status: string
  department?: string | null
  owner_id: number
}

export interface DeviceUpdate {
  hostname: string
  ip_address: string
  operating_system: string
  status: string
  department?: string | null
  owner_id: number
}
