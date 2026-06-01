export interface User {
  id: number
  username: string
  email: string
  role: string
  is_active: boolean
  created_at: string | null
}

export interface TokenResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in?: number
}
