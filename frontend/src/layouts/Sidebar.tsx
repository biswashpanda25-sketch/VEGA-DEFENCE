import { NavLink } from 'react-router-dom'
import { PRIMARY_NAV, ADMIN_NAV, canAccessAdmin } from '../navigation/navConfig'
import { useAuth } from '../store'

export default function Sidebar() {
  const user = useAuth((s) => s.user)
  const showAdmin = canAccessAdmin(user?.role)

  return (
    <aside className="sidebar">
      <nav className="nav" aria-label="Main Navigation">
        <div className="nav-section">Workspace</div>
        {PRIMARY_NAV.map((it) => {
          const Icon = it.icon
          return (
            <NavLink
              key={it.to}
              to={it.to}
              end={it.to === '/'}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
              title={it.description}
            >
              <Icon size={16} className="ico" />
              <span>{it.label}</span>
            </NavLink>
          )
        })}

        {showAdmin && (
          <>
            <div className="nav-divider" style={{ height: 1, background: 'var(--line)', margin: '14px 8px 8px' }} />
            <div className="nav-section">Governance</div>
            {(() => {
              const AdminIcon = ADMIN_NAV.icon
              return (
                <NavLink
                  to={ADMIN_NAV.to}
                  className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
                  title={ADMIN_NAV.description}
                >
                  <AdminIcon size={16} className="ico" />
                  <span>{ADMIN_NAV.label}</span>
                </NavLink>
              )
            })()}
          </>
        )}
      </nav>

      <div style={{ padding: '10px 12px', borderTop: '1px solid var(--line)' }}>
        <div className="tiny muted">Classification ceiling</div>
        <div className="row gap6" style={{ marginTop: 4 }}>
          <span className="dot amber" />
          <span className="tiny font-medium">INTERNAL · SYNTHETIC DATA</span>
        </div>
        <div className="tiny muted" style={{ marginTop: 6, fontFamily: 'var(--mono)' }}>
          build 2.0.0 · IST
        </div>
      </div>
    </aside>
  )
}
