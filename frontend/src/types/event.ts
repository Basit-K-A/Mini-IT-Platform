export interface Event {
  id: number
  event_type: string
  severity: string
  message: string
  timestamp: string
  device_id: number
}

export interface EventCreate {
  event_type: string
  severity: string
  message: string
  device_id: number
}
