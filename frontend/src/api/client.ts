/**
 * Central HTTP client — base URL from env, JWT injection, errors, dev logging.
 */

import { ApiError } from './types'

const TOKEN_KEY = 'nexventory_token'
const REFRESH_KEY = 'nexventory_refresh_token'

const isDev = import.meta.env.DEV

/**
 * API base URL (no trailing slash).
 * Default `/api` matches nginx on EC2 (location /api/ → FastAPI) and Vite dev proxy.
 */
export function getApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_URL
  if (raw === undefined || raw === '') {
    return '/api'
  }
  return String(raw).replace(/\/$/, '')
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setTokens(accessToken: string, refreshToken?: string): void {
  localStorage.setItem(TOKEN_KEY, accessToken)
  if (refreshToken) {
    localStorage.setItem(REFRESH_KEY, refreshToken)
  }
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export function clearToken(): void {
  clearTokens()
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

type UnauthorizedHandler = () => void
let onUnauthorized: UnauthorizedHandler | null = null

export function setUnauthorizedHandler(handler: UnauthorizedHandler): void {
  onUnauthorized = handler
}

function buildUrl(path: string): string {
  const base = getApiBaseUrl()
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return base ? `${base}${normalizedPath}` : normalizedPath
}

function logDev(method: string, url: string, status?: number, detail?: string): void {
  if (!isDev) return
  if (status !== undefined) {
    console.debug(`[api] ${method} ${url} → ${status}${detail ? ` (${detail})` : ''}`)
  } else {
    console.debug(`[api] ${method} ${url}`)
  }
}

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json()
    // Standardized envelope: { error, message, code, detail, errors? }
    if (typeof data.message === 'string') return data.message
    if (typeof data.detail === 'string') return data.detail
    if (Array.isArray(data.errors)) {
      return data.errors
        .map((d: { msg?: string }) => d.msg ?? JSON.stringify(d))
        .join(', ')
    }
    if (Array.isArray(data.detail)) {
      return data.detail
        .map((d: { msg?: string }) => d.msg ?? JSON.stringify(d))
        .join(', ')
    }
  } catch {
    /* ignore */
  }
  return response.statusText || 'Request failed'
}

export interface RequestOptions extends Omit<RequestInit, 'body'> {
  auth?: boolean
  body?: unknown
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { auth = true, body, headers: initHeaders, ...init } = options
  const method = (init.method ?? 'GET').toUpperCase()
  const url = buildUrl(path)
  const headers = new Headers(initHeaders)

  if (auth) {
    const token = getToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }

  let fetchBody: BodyInit | undefined
  if (body instanceof FormData || body instanceof URLSearchParams) {
    if (body instanceof URLSearchParams && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/x-www-form-urlencoded')
    }
    fetchBody = body
  } else if (body !== undefined) {
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }
    fetchBody = JSON.stringify(body)
  }

  logDev(method, url)

  let response: Response
  try {
    response = await fetch(url, {
      ...init,
      method,
      headers,
      body: fetchBody,
    })
  } catch (err) {
    const hint =
      'Could not reach the API. Start Docker (nexventory_api on port 8000), run the UI with npm run dev, and set VITE_API_URL=/api in frontend/.env (then restart Vite).'
    const detail = err instanceof Error ? err.message : String(err)
    logDev(method, url, undefined, detail)
    throw new ApiError(0, detail === 'Failed to fetch' ? hint : detail)
  }

  if (!response.ok) {
    const message = await parseError(response)
    logDev(method, url, response.status, message)

    if (response.status === 401 && auth) {
      clearTokens()
      onUnauthorized?.()
    }

    throw new ApiError(response.status, message)
  }

  logDev(method, url, response.status)

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export function toQueryString(params: Record<string, string | number | boolean | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === '') continue
    search.set(key, String(value))
  }
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}
