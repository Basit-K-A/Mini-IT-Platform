export interface PaginationMeta {
  total_records: number
  total_pages: number
  current_page: number
  page_size: number
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: PaginationMeta
}

/** Normalize list API payloads (guards against undefined `data` after schema changes). */
export function normalizePaginatedResponse<T>(raw: unknown): PaginatedResponse<T> {
  if (raw && typeof raw === 'object' && 'data' in raw) {
    const body = raw as PaginatedResponse<T>
    return {
      data: Array.isArray(body.data) ? body.data : [],
      pagination: body.pagination ?? {
        total_records: 0,
        total_pages: 1,
        current_page: 1,
        page_size: 0,
      },
    }
  }
  return {
    data: [],
    pagination: {
      total_records: 0,
      total_pages: 1,
      current_page: 1,
      page_size: 0,
    },
  }
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export interface DeviceListQuery {
  page?: number
  limit?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  status?: string
  department?: string
  owner_id?: number
  assigned_to?: number
  hostname?: string
  operating_system?: string
}

export interface AuditListQuery {
  page?: number
  limit?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  action?: string
  user_id?: number
  ip_address?: string
}
