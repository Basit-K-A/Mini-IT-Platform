import { useCallback, useEffect, useState } from 'react'
import { listEvents } from '../api/events'
import { Badge } from '../components/Badge'
import { Card } from '../components/Card'
import { EmptyState } from '../components/EmptyState'
import { ErrorMessage } from '../components/ErrorMessage'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { useAuth } from '../hooks/useAuth'
import type { Event } from '../types/event'
import { createRequestGuard } from '../utils/requestGuard'
import { severityVariant } from '../utils/status'

const loadGuard = createRequestGuard()

export function EventsPage() {
  const { user, loading: authLoading } = useAuth()
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    if (!user) return
    const requestId = loadGuard.next()
    setLoading(true)
    setError('')
    try {
      const response = await listEvents({
        page: 1,
        limit: 50,
        sort_by: 'timestamp',
        sort_order: 'desc',
      })
      if (!loadGuard.isCurrent(requestId)) return
      setEvents(response.data)
      setError('')
    } catch (err) {
      if (!loadGuard.isCurrent(requestId)) return
      setError(err instanceof Error ? err.message : 'Failed to load events')
    } finally {
      if (loadGuard.isCurrent(requestId)) setLoading(false)
    }
  }, [user])

  useEffect(() => {
    if (authLoading || !user) return
    void load()
  }, [authLoading, user, load])

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Events</h1>
          <p className="page-header__subtitle">Device event log</p>
        </div>
        <button type="button" className="btn btn--ghost" onClick={load} disabled={loading}>
          Retry
        </button>
      </header>

      <ErrorMessage message={error} />

      <Card title="Recent events">
        {loading ? (
          <LoadingSpinner label="Loading events…" />
        ) : events.length === 0 ? (
          <EmptyState title="No events" description="Events appear when devices report activity." />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Type</th>
                  <th>Severity</th>
                  <th>Device</th>
                  <th>Message</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id}>
                    <td>{new Date(event.timestamp).toLocaleString()}</td>
                    <td>{event.event_type}</td>
                    <td>
                      <Badge label={event.severity} variant={severityVariant(event.severity)} />
                    </td>
                    <td>{event.device_id}</td>
                    <td>{event.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
