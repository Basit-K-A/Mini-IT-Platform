import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge } from '../components/Badge'
import { Card } from '../components/Card'
import { ErrorMessage } from '../components/ErrorMessage'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { StatCard } from '../components/StatCard'
import { listDevices } from '../api/devices'
import { listEvents } from '../api/events'
import { useAuth } from '../hooks/useAuth'
import type { Device } from '../types/device'
import type { Event } from '../types/event'
import { createRequestGuard } from '../utils/requestGuard'
import { isOnlineStatus, severityVariant } from '../utils/status'

const loadGuard = createRequestGuard()

export function DashboardPage() {
  const { user, loading: authLoading, permissions } = useAuth()
  const canViewDevices = permissions.canViewDevices
  const [devices, setDevices] = useState<Device[]>([])
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (authLoading || !user) return

    const requestId = loadGuard.next()
    let cancelled = false

    async function load() {
      setLoading(true)
      setError('')

      const [eventsResult, devicesResult] = await Promise.allSettled([
        listEvents({ page: 1, limit: 50, sort_by: 'timestamp', sort_order: 'desc' }),
        canViewDevices
          ? listDevices({ page: 1, limit: 100, sort_by: 'created_at', sort_order: 'desc' })
          : Promise.resolve(null),
      ])

      if (cancelled || !loadGuard.isCurrent(requestId)) return

      const errors: string[] = []

      if (eventsResult.status === 'fulfilled') {
        setEvents(eventsResult.value.data)
      } else {
        const reason = eventsResult.reason
        errors.push(
          reason instanceof Error ? reason.message : 'Failed to load events',
        )
        setEvents([])
      }

      if (devicesResult.status === 'fulfilled' && devicesResult.value) {
        setDevices(devicesResult.value.data)
      } else if (canViewDevices) {
        if (devicesResult.status === 'rejected') {
          const reason = devicesResult.reason
          errors.push(
            reason instanceof Error ? reason.message : 'Failed to load devices',
          )
        }
        setDevices([])
      } else {
        setDevices([])
      }

      setError(errors.join(' · '))
      setLoading(false)
    }

    void load()

    return () => {
      cancelled = true
    }
  }, [authLoading, user, canViewDevices])

  const online = devices.filter((d) => isOnlineStatus(d.status)).length
  const offline = devices.length - online
  const recentEvents = events.slice(0, 8)

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="page-header__subtitle">Infrastructure overview</p>
        </div>
      </header>

      <ErrorMessage message={error} />

      {loading ? (
        <LoadingSpinner label="Loading dashboard…" />
      ) : (
        <>
          <div className="stat-grid">
            {canViewDevices && (
              <>
                <StatCard label="Total devices" value={devices.length} />
                <StatCard label="Online" value={online} accent="success" />
                <StatCard
                  label="Offline / other"
                  value={offline}
                  accent={offline > 0 ? 'warning' : 'default'}
                />
              </>
            )}
            <StatCard label="Security events" value={events.length} hint="All recorded events" />
          </div>

          <div className="dashboard-grid">
            <Card title="Recent security events">
              {recentEvents.length === 0 ? (
                <p className="muted">No events yet.</p>
              ) : (
                <ul className="event-feed">
                  {recentEvents.map((event) => (
                    <li key={event.id} className="event-feed__item">
                      <div className="event-feed__meta">
                        <Badge label={event.severity} variant={severityVariant(event.severity)} />
                        <span className="event-feed__type">{event.event_type}</span>
                        <time dateTime={event.timestamp}>
                          {new Date(event.timestamp).toLocaleString()}
                        </time>
                      </div>
                      <p className="event-feed__message">{event.message}</p>
                      <p className="event-feed__device">Device #{event.device_id}</p>
                    </li>
                  ))}
                </ul>
              )}
              <Link to="/events" className="link-inline">
                View all events →
              </Link>
            </Card>

            {canViewDevices && (
              <Card title="Device snapshot">
                {devices.length === 0 ? (
                  <p className="muted">No devices registered.</p>
                ) : (
                  <ul className="device-snapshot">
                    {devices.slice(0, 6).map((device) => (
                      <li key={device.id}>
                        <span className="device-snapshot__host">{device.hostname}</span>
                        <span className="device-snapshot__ip">{device.ip_address}</span>
                        <Badge
                          label={device.status}
                          variant={isOnlineStatus(device.status) ? 'success' : 'danger'}
                        />
                      </li>
                    ))}
                  </ul>
                )}
                <Link to="/devices" className="link-inline">
                  Manage devices →
                </Link>
              </Card>
            )}
          </div>
        </>
      )}
    </div>
  )
}
