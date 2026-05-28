const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const TOKEN_KEY = 'nexventory_token'

export function getApiUrl(): string {
  return API_URL.replace(/\/$/, '')
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json()
    if (typeof data.detail === 'string') return data.detail
    if (Array.isArray(data.detail)) {
      return data.detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join(', ')
    }
  } catch {
    /* ignore */
  }
  return response.statusText || 'Request failed'
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  auth = true,
): Promise<T> {
  const headers = new Headers(options.headers)

  if (auth) {
    const token = getToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }

  if (options.body && !(options.body instanceof FormData)) {
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }
  }

  const response = await fetch(`${getApiUrl()}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    throw new ApiError(response.status, await parseError(response))
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}
