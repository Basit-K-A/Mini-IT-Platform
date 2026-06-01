/**
 * Auth API — maps to FastAPI routes:
 *   POST /register
 *   POST /token        (login; OAuth2 form)
 *   GET  /users/me/    (current user)
 */

import type { TokenResponse, User } from '../types/user'
import { apiRequest, clearTokens, getApiBaseUrl, setTokens } from './client'

export interface RegisterPayload {
  username: string
  email: string
  password: string
}

/** Login — backend uses POST /token with form-urlencoded credentials */
export async function login(username: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams()
  body.set('username', username)
  body.set('password', password)

  const response = await fetch(`${getApiBaseUrl()}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })

  if (!response.ok) {
    let message = 'Login failed'
    try {
      const data = await response.json()
      if (typeof data.message === 'string') message = data.message
      else if (typeof data.detail === 'string') message = data.detail
    } catch {
      /* ignore */
    }
    throw new Error(message)
  }

  const token = (await response.json()) as TokenResponse
  setTokens(token.access_token, token.refresh_token)
  return token
}

export function register(payload: RegisterPayload): Promise<User> {
  return apiRequest<User>('/register', {
    method: 'POST',
    auth: false,
    body: payload,
  })
}

/** Current user — GET /users/me/ */
export function fetchCurrentUser(): Promise<User> {
  return apiRequest<User>('/users/me/')
}

export function logout(): void {
  clearTokens()
}
