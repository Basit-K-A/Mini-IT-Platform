import { useEffect, useState } from 'react'
import { Badge } from '../components/Badge'
import { Card } from '../components/Card'
import { ErrorMessage } from '../components/ErrorMessage'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { listEvents } from '../services/events'
import type { Event } from '../types/event'
import { severityVariant } from '../utils/status'

export function EventsPage() {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError('')
      try {
        const data = await listEvents()
        if (!cancelled) {
          setEvents(
            [...data].sort(
              (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
            ),
          )
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load events')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Events</h1>
          <p className="page-header__subtitle">Security and infrastructure event log</p>
        </div>
      </header>

      <ErrorMessage message={error} />

      <Card title={`All events (${events.length})`}>
        {loading ? (
          <LoadingSpinner label="Loading events…" />
        ) : events.length === 0 ? (
          <p className="muted">No events recorded. Create events via the API or Swagger.</p>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Severity</th>
                  <th>Message</th>
                  <th>Device</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id}>
                    <td>{event.event_type}</td>
                    <td>
                      <Badge label={event.severity} variant={severityVariant(event.severity)} />
                    </td>
                    <td className="data-table__message">{event.message}</td>
                    <td>
                      <code>#{event.device_id}</code>
                    </td>
                    <td>
                      <time dateTime={event.timestamp}>
                        {new Date(event.timestamp).toLocaleString()}
                      </time>
                    </td>
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
