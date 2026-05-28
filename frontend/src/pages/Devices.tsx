import { useEffect, useState, type FormEvent } from 'react'
import { Badge } from '../components/Badge'
import { Card } from '../components/Card'
import { ErrorMessage } from '../components/ErrorMessage'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { useAuth } from '../hooks/useAuth'
import { createDevice, listDevices } from '../services/devices'
import type { Device } from '../types/device'
import { deviceStatusVariant } from '../utils/status'

const emptyForm = {
  hostname: '',
  ip_address: '',
  operating_system: '',
  status: 'active',
}

export function DevicesPage() {
  const { user } = useAuth()
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [form, setForm] = useState(emptyForm)
  const [submitting, setSubmitting] = useState(false)
  const [showForm, setShowForm] = useState(false)

  async function loadDevices() {
    setLoading(true)
    setError('')
    try {
      setDevices(await listDevices())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load devices')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDevices()
  }, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!user) return
    setSubmitting(true)
    setError('')
    try {
      await createDevice({ ...form, owner_id: user.id })
      setForm(emptyForm)
      setShowForm(false)
      await loadDevices()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create device')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Devices</h1>
          <p className="page-header__subtitle">Managed infrastructure inventory</p>
        </div>
        <button type="button" className="btn btn--primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? 'Cancel' : 'Add device'}
        </button>
      </header>

      <ErrorMessage message={error} />

      {showForm ? (
        <Card title="Add device" className="form-card">
          <form className="form form--grid" onSubmit={handleSubmit}>
            <label className="form__field">
              <span>Hostname</span>
              <input
                required
                value={form.hostname}
                onChange={(e) => setForm({ ...form, hostname: e.target.value })}
              />
            </label>
            <label className="form__field">
              <span>IP address</span>
              <input
                required
                value={form.ip_address}
                onChange={(e) => setForm({ ...form, ip_address: e.target.value })}
              />
            </label>
            <label className="form__field">
              <span>Operating system</span>
              <input
                required
                value={form.operating_system}
                onChange={(e) => setForm({ ...form, operating_system: e.target.value })}
              />
            </label>
            <label className="form__field">
              <span>Status</span>
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
              >
                <option value="active">active</option>
                <option value="online">online</option>
                <option value="offline">offline</option>
                <option value="maintenance">maintenance</option>
                <option value="inactive">inactive</option>
              </select>
            </label>
            <div className="form__actions">
              <button type="submit" className="btn btn--primary" disabled={submitting}>
                {submitting ? 'Saving…' : 'Save device'}
              </button>
            </div>
          </form>
        </Card>
      ) : null}

      <Card title={`All devices (${devices.length})`}>
        {loading ? (
          <LoadingSpinner label="Loading devices…" />
        ) : devices.length === 0 ? (
          <p className="muted">No devices yet. Add your first device above.</p>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Hostname</th>
                  <th>IP address</th>
                  <th>OS</th>
                  <th>Status</th>
                  <th>Owner ID</th>
                </tr>
              </thead>
              <tbody>
                {devices.map((device) => (
                  <tr key={device.id}>
                    <td>{device.hostname}</td>
                    <td>
                      <code>{device.ip_address}</code>
                    </td>
                    <td>{device.operating_system}</td>
                    <td>
                      <Badge label={device.status} variant={deviceStatusVariant(device.status)} />
                    </td>
                    <td>{device.owner_id}</td>
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
