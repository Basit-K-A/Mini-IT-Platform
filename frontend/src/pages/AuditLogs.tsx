import { useCallback, useEffect, useMemo, useState } from 'react'
import { listAuditLogs } from '../api/audit'
import type { AuditListQuery, PaginationMeta } from '../api/types'
import { Card } from '../components/Card'
import { EmptyState } from '../components/EmptyState'
import { ErrorMessage } from '../components/ErrorMessage'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { Pagination } from '../components/Pagination'
import { useAuth } from '../hooks/useAuth'
import type { AuditLog } from '../types/audit'
import { createRequestGuard } from '../utils/requestGuard'

const loadGuard = createRequestGuard()

export function AuditLogsPage() {
  const { user, loading: authLoading } = useAuth()
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [pagination, setPagination] = useState<PaginationMeta | null>(null)
  const [query, setQuery] = useState<AuditListQuery>({
    page: 1,
    limit: 20,
    sort_by: 'timestamp',
    sort_order: 'desc',
  })
  const [actionFilter, setActionFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const queryKey = useMemo(
    () => JSON.stringify({ ...query, action: actionFilter || undefined }),
    [query, actionFilter],
  )

  const load = useCallback(async () => {
    if (!user) return
    const requestId = loadGuard.next()
    setLoading(true)
    setError('')
    try {
      const response = await listAuditLogs({
        ...query,
        action: actionFilter || undefined,
      })
      if (!loadGuard.isCurrent(requestId)) return
      setLogs(response.data)
      setPagination(response.pagination)
      setError('')
    } catch (err) {
      if (!loadGuard.isCurrent(requestId)) return
      setError(err instanceof Error ? err.message : 'Failed to load audit logs')
    } finally {
      if (loadGuard.isCurrent(requestId)) setLoading(false)
    }
  }, [user, query, actionFilter])

  useEffect(() => {
    if (authLoading || !user) return
    void load()
  }, [authLoading, user, queryKey, load])

  function applyFilters(e: React.FormEvent) {
    e.preventDefault()
    setQuery((q) => ({ ...q, page: 1 }))
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Audit logs</h1>
          <p className="page-header__subtitle">Security trail (admin / analyst)</p>
        </div>
        <button type="button" className="btn btn--ghost" onClick={() => load()} disabled={loading}>
          Retry
        </button>
      </header>

      <Card title="Filters" className="form-card">
        <form className="form form--grid" onSubmit={applyFilters}>
          <label className="form__field">
            <span>Action</span>
            <input
              placeholder="e.g. LOGIN_FAILED"
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
            />
          </label>
          <div className="form__actions">
            <button type="submit" className="btn btn--primary">
              Apply
            </button>
          </div>
        </form>
      </Card>

      <ErrorMessage message={error} />

      <Card title="Recent activity">
        {loading ? (
          <LoadingSpinner label="Loading audit logs…" />
        ) : logs.length === 0 ? (
          <EmptyState
            title="No audit entries"
            description="Try adjusting filters or check back after API activity."
          />
        ) : (
          <>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>Endpoint</th>
                    <th>IP</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id}>
                      <td>{new Date(log.timestamp).toLocaleString()}</td>
                      <td>{log.user_id ?? '—'}</td>
                      <td>
                        <code>{log.action}</code>
                      </td>
                      <td>{log.endpoint}</td>
                      <td>
                        <code>{log.ip_address}</code>
                      </td>
                      <td>{log.status_code}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {pagination ? (
              <Pagination
                meta={pagination}
                disabled={loading}
                onPageChange={(page) => setQuery((q) => ({ ...q, page }))}
              />
            ) : null}
          </>
        )}
      </Card>
    </div>
  )
}
