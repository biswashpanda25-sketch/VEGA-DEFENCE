import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api, fmtDate, roleLabel, type SearchHit } from '../api'
import { useAuth, useUI } from '../store'
import { IcBell, IcLogout, IcSearch } from '../components/icons'
import { Badge } from '../components/ui'

function TopSearch() {
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const nav = useNavigate()

  const { data } = useQuery({
    queryKey: ['typeahead', q],
    queryFn: () => api.get<{ results: SearchHit[] }>(`/search?q=${encodeURIComponent(q)}&limit=6`),
    enabled: q.trim().length > 1,
    staleTime: 15_000,
  })

  return (
    <div className="searchbox" style={{ position: 'relative' }}>
      <IcSearch size={14} />
      <input
        className="input"
        placeholder="Search records or ask VEGA…"
        value={q}
        onChange={(e) => {
          setQ(e.target.value)
          setOpen(true)
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && q.trim()) {
            nav(`/ask?tab=search&q=${encodeURIComponent(q.trim())}`)
            setOpen(false)
          }
          if (e.key === 'Escape') setOpen(false)
        }}
        onBlur={() => setTimeout(() => setOpen(false), 180)}
        aria-label="Global search or ask VEGA"
      />
      {open && q.trim().length > 1 && (
        <div
          style={{
            position: 'absolute',
            top: 38,
            left: 0,
            right: 0,
            background: 'var(--panel)',
            border: '1px solid var(--line-2)',
            borderRadius: 3,
            zIndex: 60,
            maxHeight: 320,
            overflowY: 'auto',
            boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
          }}
        >
          {(data?.results ?? []).map((r) => (
            <button
              key={`${r.kind}-${r.id}`}
              className="row between"
              style={{
                width: '100%',
                textAlign: 'left',
                background: 'transparent',
                border: 'none',
                borderBottom: '1px solid var(--line)',
                padding: '8px 12px',
                color: 'var(--text)',
                cursor: 'pointer',
              }}
              onMouseDown={() => {
                nav(`/ask?tab=search&q=${encodeURIComponent(r.title)}`)
                setOpen(false)
              }}
            >
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {r.title}
              </span>
              <Badge tone="neutral">{r.kind}</Badge>
            </button>
          ))}
          {data && data.results.length === 0 && (
            <div className="empty" style={{ padding: 14 }}>
              No authorized matches found
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function NotificationBell() {
  const [open, setOpen] = useState(false)
  const nav = useNavigate()
  const { data } = useQuery({
    queryKey: ['notif-bell'],
    queryFn: () => api.get<any[]>('/notifications'),
    refetchInterval: 60_000,
  })
  const unread = (data ?? []).filter((n) => !n.is_read).length

  return (
    <div style={{ position: 'relative' }}>
      <button
        className="btn ghost"
        onClick={() => setOpen((o) => !o)}
        aria-label="Notifications"
        style={{ padding: '5px 8px', position: 'relative' }}
      >
        <IcBell size={15} />
        {unread > 0 && (
          <span
            className="badge red"
            style={{
              marginLeft: 4,
              fontSize: 10,
              padding: '1px 5px',
              borderRadius: 8,
            }}
          >
            {unread}
          </span>
        )}
      </button>

      {open && (
        <div
          style={{
            position: 'absolute',
            right: 0,
            top: 36,
            width: 360,
            background: 'var(--panel)',
            border: '1px solid var(--line-2)',
            borderRadius: 4,
            zIndex: 70,
            maxHeight: 400,
            overflowY: 'auto',
            boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
          }}
        >
          <div className="card-h">
            <span className="card-t">Operational Alerts &amp; Updates</span>
            <button
              className="btn sm ghost"
              onClick={() => {
                nav('/?tab=activity')
                setOpen(false)
              }}
            >
              View all
            </button>
          </div>
          {(data ?? []).slice(0, 6).map((n) => (
            <div
              key={n.id}
              style={{
                padding: '9px 12px',
                borderBottom: '1px solid var(--line)',
                background: n.is_read ? 'transparent' : 'rgba(217,119,6,0.04)',
              }}
            >
              <div className="row between gap8">
                <span style={{ fontSize: 12, fontWeight: n.is_read ? 400 : 600 }}>
                  {n.title}
                </span>
                <Badge tone={n.severity}>{n.severity}</Badge>
              </div>
              <div className="tiny muted" style={{ marginTop: 3 }}>
                {n.message}
              </div>
              <div className="tiny muted" style={{ marginTop: 2 }}>
                {fmtDate(n.created_at)}
              </div>
            </div>
          ))}
          {(!data || data.length === 0) && <div className="empty">No notifications</div>}
        </div>
      )}
    </div>
  )
}

export default function Topbar() {
  const { user, clear } = useAuth()
  const { theme, toggleTheme } = useUI()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className="topbar">
      <div className="brand">
        <div className="brand-mark">VD</div>
        <div>
          <div className="brand-name">VEGA DEFENCE</div>
          <div className="brand-sub">SOVEREIGN MILITARY INTELLIGENCE PLATFORM</div>
        </div>
      </div>

      <TopSearch />

      <div className="row gap8" style={{ marginLeft: 'auto' }}>
        <select
          className="input"
          style={{ width: 220, padding: '5px 8px', fontSize: 11.5 }}
          value={user?.organization_id ?? ''}
          onChange={() => {}}
          aria-label="Active Organisation Context"
        >
          <option value={user?.organization_id ?? ''}>
            {user?.role === 'platform_admin'
              ? 'All commands (platform scope)'
              : 'Northern Tactical Command (scoped)'}
          </option>
        </select>

        <button
          className="btn ghost sm"
          onClick={toggleTheme}
          title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
          style={{ padding: '4px 8px', display: 'flex', alignItems: 'center', gap: 5 }}
        >
          {theme === 'light' ? '🌙 Dark' : '☀️ Light'}
        </button>

        <NotificationBell />

        <div style={{ position: 'relative' }}>
          <button
            className="btn ghost"
            onClick={() => setMenuOpen((o) => !o)}
            style={{ padding: '4px 9px' }}
          >
            <span className="dot green" />
            <span style={{ fontSize: 12, fontWeight: 500 }}>
              {user?.full_name?.split(' ')[0] ?? 'User'}
            </span>
            <span className="tiny muted">{roleLabel(user?.role ?? '')}</span>
          </button>

          {menuOpen && (
            <div
              style={{
                position: 'absolute',
                right: 0,
                top: 36,
                width: 250,
                background: 'var(--panel)',
                border: '1px solid var(--line-2)',
                borderRadius: 4,
                zIndex: 80,
                boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
              }}
            >
              <div style={{ padding: '10px 12px', borderBottom: '1px solid var(--line)' }}>
                <div style={{ fontSize: 12, fontWeight: 600 }}>{user?.full_name}</div>
                <div className="tiny muted">{user?.email}</div>
                <div className="tiny muted" style={{ marginTop: 4 }}>
                  Role: <Badge tone="neutral">{roleLabel(user?.role ?? '')}</Badge>
                </div>
              </div>
              <button
                className="row gap8"
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text)',
                  cursor: 'pointer',
                  fontSize: 12,
                }}
                onClick={() => {
                  api.post('/auth/logout').catch(() => {})
                  clear()
                }}
              >
                <IcLogout size={14} /> Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
