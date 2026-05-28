import type { TokenResponse, User } from '../types/user'
import { apiRequest, setToken } from './api'

export async function login(username: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams()
  body.set('username', username)
  body.set('password', password)

  const response = await fetch(`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })

  if (!response.ok) {
    let message = 'Login failed'
    try {
      const data = await response.json()
      if (typeof data.detail === 'string') message = data.detail
    } catch {
      /* ignore */
    }
    throw new Error(message)
  }

  const token = (await response.json()) as TokenResponse
  setToken(token.access_token)
  return token
}

export function fetchCurrentUser(): Promise<User> {
  return apiRequest<User>('/users/me/')
}
