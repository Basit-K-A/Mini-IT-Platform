import { create } from 'zustand'
import * as devicesApi from '../api/devices'
import type { DeviceListQuery, PaginationMeta } from '../api/types'
import type { Device } from '../types/device'
import { createRequestGuard } from '../utils/requestGuard'

const fetchGuard = createRequestGuard()

interface DevicesState {
  devices: Device[]
  pagination: PaginationMeta | null
  query: DeviceListQuery
  loading: boolean
  error: string | null
  setQuery: (partial: Partial<DeviceListQuery>) => void
  fetchDevices: () => Promise<void>
  resetError: () => void
}

const defaultQuery: DeviceListQuery = {
  page: 1,
  limit: 10,
  sort_by: 'created_at',
  sort_order: 'desc',
}

export const useDevicesStore = create<DevicesState>((set, get) => ({
  devices: [],
  pagination: null,
  query: { ...defaultQuery },
  loading: false,
  error: null,

  setQuery: (partial) => {
    set((state) => ({
      query: { ...state.query, ...partial },
    }))
  },

  resetError: () => set({ error: null }),

  fetchDevices: async () => {
    const requestId = fetchGuard.next()
    set({ loading: true, error: null })
    try {
      const response = await devicesApi.listDevices(get().query)
      if (!fetchGuard.isCurrent(requestId)) return
      set({
        devices: response.data,
        pagination: response.pagination,
        loading: false,
        error: null,
      })
    } catch (err) {
      if (!fetchGuard.isCurrent(requestId)) return
      set({
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to load devices',
      })
    }
  },
}))
