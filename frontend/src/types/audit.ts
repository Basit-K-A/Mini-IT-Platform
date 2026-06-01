export interface AuditLog {
  id: number
  user_id: number | null
  action: string
  endpoint: string
  ip_address: string
  status_code: number
  timestamp: string
  details: string | null
}
