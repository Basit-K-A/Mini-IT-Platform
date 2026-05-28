import { NavLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const links = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/devices', label: 'Devices', end: false },
  { to: '/events', label: 'Events', end: false },
]

export function Sidebar() {
  const { user, logout } = useAuth()

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <span className="sidebar__logo" aria-hidden="true">
          N
        </span>
        <div>
          <p className="sidebar__name">Nexventory</p>
          <p className="sidebar__tagline">Infrastructure Console</p>
        </div>
      </div>

      <nav className="sidebar__nav" aria-label="Main">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) =>
              `sidebar__link${isActive ? ' sidebar__link--active' : ''}`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar__footer">
        <p className="sidebar__user">{user?.username ?? '—'}</p>
        <button type="button" className="btn btn--ghost btn--small" onClick={logout}>
          Sign out
        </button>
      </div>
    </aside>
  )
}
