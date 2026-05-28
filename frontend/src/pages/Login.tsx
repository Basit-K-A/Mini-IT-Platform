import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { ErrorMessage } from '../components/ErrorMessage'
import { useAuth } from '../hooks/useAuth'
import { login } from '../services/auth'

export function LoginPage() {
  const navigate = useNavigate()
  const { isAuthenticated, refreshUser, loading } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!loading && isAuthenticated) {
    return <Navigate to="/" replace />
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(username, password)
      await refreshUser()
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-card__header">
          <span className="login-card__logo" aria-hidden="true">
            N
          </span>
          <h1>Nexventory</h1>
          <p>Infrastructure &amp; security dashboard</p>
        </div>

        <ErrorMessage message={error} />

        <form className="form" onSubmit={handleSubmit}>
          <label className="form__field">
            <span>Username</span>
            <input
              type="text"
              name="username"
              autoComplete="username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>
          <label className="form__field">
            <span>Password</span>
            <input
              type="password"
              name="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <button type="submit" className="btn btn--primary btn--full" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="login-card__hint">
          Use credentials from <code>POST /register</code> or Swagger at{' '}
          <code>/docs</code>.
        </p>
      </div>
    </div>
  )
}
