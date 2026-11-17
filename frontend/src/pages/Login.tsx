import { useState } from 'react'
import { api, roleLabel } from '../api'
import { useAuth } from '../store'
import { IcChevron, IcEye, IcEyeOff, IcLock, IcShield } from '../components/icons'

interface DemoAccount {
  email: string
  role: string
  command: string
  clearance: 'PROTECTED' | 'RESTRICTED' | 'INTERNAL'
}

const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    email: 'analyst@gotham-demo.in',
    role: 'Lead Intelligence Officer',
    command: 'Northern Tactical Command',
    clearance: 'RESTRICTED',
  },
  {
    email: 'reviewer@gotham-demo.in',
    role: 'Operations Reviewer',
    command: 'Flag Officer Authority',
    clearance: 'RESTRICTED',
  },
  {
    email: 'admin@gotham-demo.in',
    role: 'Command Administrator',
    command: 'Integrated Defence Staff (HQ IDS)',
    clearance: 'PROTECTED',
  },
  {
    email: 'disaster@gotham-demo.in',
    role: 'Maritime Tactical Analyst',
    command: 'Eastern Naval Command',
    clearance: 'INTERNAL',
  },
]

export default function Login() {
  const [email, setEmail] = useState('analyst@gotham-demo.in')
  const [password, setPassword] = useState('Gotham@2026')
  const [showPassword, setShowPassword] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [showDemo, setShowDemo] = useState(false)
  const setAuth = useAuth((s) => s.setAuth)

  async function submit(e?: React.FormEvent) {
    if (e) e.preventDefault()
    setErr(null)
    setBusy(true)
    try {
      const r = await api.post<{ access_token: string }>('/auth/login', { email, password })
      // Token must be in the store before authenticated calls; hydrate identity immediately after.
      setAuth(r.access_token, {
        id: '',
        email,
        full_name: email,
        role: '',
        organization_id: null,
        is_active: true,
      })
      const me = await api.get<any>('/auth/me')
      setAuth(r.access_token, me)
    } catch (e: any) {
      setErr(e.message ?? 'Invalid institutional credentials. Access attempt has been audited.')
    } finally {
      setBusy(false)
    }
  }

  function handleSelectDemo(acc: DemoAccount) {
    setEmail(acc.email)
    setPassword('Gotham@2026')
    setErr(null)
  }

  return (
    <div className="vega-login-root">
      {/* -------------------- LEFT COLUMN: BRAND & PLATFORM OVERVIEW -------------------- */}
      <section className="vega-login-left">
        {/* Subtle SVG Topography and Tactical Coordinates Background */}
        <div className="vega-grid-overlay" />
        <svg
          className="vega-topography-bg"
          viewBox="0 0 1000 800"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M-50,200 C150,150 250,300 450,220 C650,140 750,280 950,200 C1050,160 1150,240 1200,210"
            stroke="#8298AE"
            strokeWidth="1.2"
          />
          <path
            d="M-50,320 C180,260 280,410 480,340 C680,270 780,390 980,320 C1080,280 1180,360 1200,330"
            stroke="#8298AE"
            strokeWidth="1.2"
          />
          <path
            d="M-50,440 C120,380 220,530 420,460 C620,390 720,510 920,440 C1020,400 1120,480 1200,450"
            stroke="#8298AE"
            strokeWidth="1.2"
          />
          <path
            d="M-50,560 C160,500 260,650 460,580 C660,510 760,630 960,560 C1060,520 1160,600 1200,570"
            stroke="#8298AE"
            strokeWidth="1.2"
          />
          <circle cx="480" cy="340" r="4" fill="#D5A13C" />
          <circle cx="480" cy="340" r="16" stroke="#D5A13C" strokeWidth="0.8" strokeDasharray="3 3" />
          <circle cx="780" cy="390" r="3" fill="#8298AE" />
          <line x1="480" y1="20" x2="480" y2="780" stroke="#8298AE" strokeWidth="0.4" strokeDasharray="4 4" />
          <line x1="20" y1="340" x2="980" y2="340" stroke="#8298AE" strokeWidth="0.4" strokeDasharray="4 4" />
        </svg>

        {/* Top: Header branding & tactical coordinates */}
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div className="row between" style={{ marginBottom: 32, flexWrap: 'wrap', gap: 12 }}>
            <div className="row gap12">
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 3,
                  border: '1px solid #D5A13C',
                  background: 'rgba(213, 161, 60, 0.12)',
                  display: 'grid',
                  placeItems: 'center',
                  color: '#D5A13C',
                  fontWeight: 700,
                  fontSize: 13,
                  letterSpacing: '0.08em',
                  boxShadow: '0 0 12px rgba(213, 161, 60, 0.2)',
                }}
              >
                VD
              </div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: '0.18em', color: '#E9EEF4' }}>
                  VEGA DEFENCE
                </div>
                <div style={{ fontSize: 10, letterSpacing: '0.08em', color: '#8298AE', marginTop: 1 }}>
                  SOVEREIGN MILITARY INTELLIGENCE &amp; DECISION SUPPORT
                </div>
              </div>
            </div>

            <div
              className="row gap6"
              style={{
                background: 'rgba(17, 29, 41, 0.8)',
                border: '1px solid #1E2D3D',
                borderRadius: 3,
                padding: '4px 9px',
                fontSize: 10.5,
                fontFamily: 'var(--mono)',
                color: '#8298AE',
              }}
            >
              <span className="dot green" style={{ width: 5, height: 5 }} />
              <span>GRID: 20°18'N 85°37'E // AIR-GAPPED DEMO</span>
            </div>
          </div>

          {/* Main Headline */}
          <div style={{ maxWidth: 580, marginTop: 24 }}>
            <h1
              style={{
                fontSize: 32,
                fontWeight: 600,
                lineHeight: 1.25,
                letterSpacing: '-0.01em',
                color: '#E9EEF4',
                margin: 0,
              }}
            >
              Clarity in complexity.
              <br />
              <span style={{ color: '#D5A13C' }}>Confidence in decisions.</span>
            </h1>
            <p
              style={{
                color: '#8298AE',
                fontSize: 14,
                lineHeight: 1.65,
                marginTop: 16,
                maxWidth: 520,
              }}
            >
              A unified intelligence environment for authorised defence institutions to integrate
              information, examine evidence, understand complex situations and support informed
              decisions.
            </p>
          </div>
        </div>

        {/* Middle: Four Feature Blocks */}
        <div
          className="grid g2"
          style={{
            maxWidth: 620,
            margin: '36px 0',
            position: 'relative',
            zIndex: 1,
            gap: 14,
          }}
        >
          <div className="vega-feature-card">
            <div className="row gap8" style={{ marginBottom: 5 }}>
              <span className="dot teal" style={{ width: 6, height: 6 }} />
              <span style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', color: '#E9EEF4' }}>
                COMMAND ISOLATION
              </span>
            </div>
            <div style={{ fontSize: 11.5, color: '#8298AE', lineHeight: 1.5 }}>
              Organisation-scoped information access enforced strictly at query layer.
            </div>
          </div>

          <div className="vega-feature-card">
            <div className="row gap8" style={{ marginBottom: 5 }}>
              <span className="dot amber" style={{ width: 6, height: 6 }} />
              <span style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', color: '#E9EEF4' }}>
                EVIDENCE INTEGRITY
              </span>
            </div>
            <div style={{ fontSize: 11.5, color: '#8298AE', lineHeight: 1.5 }}>
              Traceable supporting records and verified empirical citations for every claim.
            </div>
          </div>

          <div className="vega-feature-card">
            <div className="row gap8" style={{ marginBottom: 5 }}>
              <span className="dot blue" style={{ width: 6, height: 6 }} />
              <span style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', color: '#E9EEF4' }}>
                AUDIT TRANSPARENCY
              </span>
            </div>
            <div style={{ fontSize: 11.5, color: '#8298AE', lineHeight: 1.5 }}>
              Recorded institutional activities, tamper-evident cryptographic chains, and approvals.
            </div>
          </div>

          <div className="vega-feature-card">
            <div className="row gap8" style={{ marginBottom: 5 }}>
              <span className="dot green" style={{ width: 6, height: 6 }} />
              <span style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', color: '#E9EEF4' }}>
                CONTROLLED AUTHORITY
              </span>
            </div>
            <div style={{ fontSize: 11.5, color: '#8298AE', lineHeight: 1.5 }}>
              Permission-based institutional workflows requiring explicit reviewer sign-off.
            </div>
          </div>
        </div>

        {/* Bottom: Institutional Security Disclaimer */}
        <div
          style={{
            fontSize: 11,
            color: '#55687A',
            borderTop: '1px solid #1E2D3D',
            paddingTop: 16,
            position: 'relative',
            zIndex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 8,
          }}
        >
          <span>Demonstration environment. All operational records and military entities are synthetic.</span>
          <span className="mono" style={{ fontSize: 10 }}>SECURITY LEVEL: CLASSIFIED-RESTRICTED</span>
        </div>
      </section>

      {/* -------------------- RIGHT COLUMN: AUTHENTICATION CONSOLE -------------------- */}
      <section className="vega-login-right">
        <form className="vega-login-card" onSubmit={submit} aria-label="Institutional Authentication Form">
          <div style={{ marginBottom: 24 }}>
            <div className="row gap8" style={{ marginBottom: 6 }}>
              <IcShield size={16} style={{ color: '#D5A13C' }} />
              <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.12em', color: '#D5A13C', textTransform: 'uppercase' }}>
                Defence Authentication Gateway
              </span>
            </div>
            <h2 style={{ fontSize: 22, fontWeight: 600, color: '#E9EEF4', margin: '4px 0 0 0', letterSpacing: '-0.01em' }}>
              Welcome to VEGA
            </h2>
            <p style={{ fontSize: 12.5, color: '#8298AE', margin: '4px 0 0 0' }}>
              Secure institutional access.
            </p>
          </div>

          {err && (
            <div
              style={{
                padding: '10px 12px',
                background: 'rgba(220, 38, 38, 0.1)',
                border: '1px solid rgba(220, 38, 38, 0.3)',
                borderRadius: 4,
                color: '#f87171',
                fontSize: 12,
                marginBottom: 16,
                lineHeight: 1.4,
              }}
            >
              {err}
            </div>
          )}

          {/* Email input */}
          <div style={{ marginBottom: 16 }}>
            <label className="vega-login-label" htmlFor="email">
              Institutional email
            </label>
            <div className="vega-input-wrap">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                <rect width="20" height="16" x="2" y="4" rx="2" />
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
              </svg>
              <input
                id="email"
                className="vega-login-input"
                type="email"
                placeholder="officer@command.gov.in"
                value={email}
                autoComplete="username"
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Password input with visibility toggle */}
          <div style={{ marginBottom: 20 }}>
            <label className="vega-login-label" htmlFor="password">
              Password
            </label>
            <div className="vega-input-wrap">
              <IcLock size={15} />
              <input
                id="password"
                className="vega-login-input"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••••••"
                value={password}
                autoComplete="current-password"
                onChange={(e) => setPassword(e.target.value)}
                style={{ paddingRight: 38 }}
                required
              />
              <button
                type="button"
                className="vega-input-toggle"
                onClick={() => setShowPassword((v) => !v)}
                title={showPassword ? 'Hide password' : 'Show password'}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <IcEyeOff size={16} /> : <IcEye size={16} />}
              </button>
            </div>
          </div>

          {/* Submit Sign In button */}
          <button className="vega-login-btn" type="submit" disabled={busy}>
            {busy ? (
              <>
                <span className="spinner" style={{ width: 14, height: 14, borderTopColor: '#0B1118' }} />
                <span>Verifying credentials…</span>
              </>
            ) : (
              <span>Sign In</span>
            )}
          </button>

          {/* Security statement */}
          <div
            style={{
              marginTop: 18,
              padding: '10px 12px',
              background: 'rgba(17, 29, 41, 0.6)',
              border: '1px solid #1E2D3D',
              borderRadius: 4,
              fontSize: 11,
              color: '#8298AE',
              lineHeight: 1.45,
              display: 'flex',
              gap: 8,
              alignItems: 'flex-start',
            }}
          >
            <IcShield size={14} style={{ color: '#8298AE', flex: '0 0 auto', marginTop: 1 }} />
            <span>Access is restricted to authorised institutional users. Authentication activity is logged.</span>
          </div>

          {/* -------------------- DEMONSTRATION IDENTITIES ACCORDION -------------------- */}
          <div style={{ marginTop: 22 }}>
            <button
              type="button"
              className="vega-demo-toggle"
              onClick={() => setShowDemo((v) => !v)}
              aria-expanded={showDemo}
            >
              <div className="row gap6">
                <span className="dot amber" style={{ width: 5, height: 5 }} />
                <span style={{ fontWeight: 500 }}>View demonstration accounts</span>
              </div>
              <div
                style={{
                  transform: showDemo ? 'rotate(90deg)' : 'rotate(0deg)',
                  transition: 'transform 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <IcChevron size={14} />
              </div>
            </button>

            {showDemo && (
              <div
                style={{
                  marginTop: 10,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                  paddingTop: 4,
                }}
              >
                {DEMO_ACCOUNTS.map((acc) => (
                  <div
                    key={acc.email}
                    className="vega-demo-card"
                    onClick={() => handleSelectDemo(acc)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        handleSelectDemo(acc)
                      }
                    }}
                  >
                    <div className="row between">
                      <span style={{ fontSize: 12, fontWeight: 600, color: '#E9EEF4' }}>
                        {acc.role}
                      </span>
                      <span
                        className={
                          acc.clearance === 'PROTECTED'
                            ? 'vega-badge-gold'
                            : 'vega-badge-steel'
                        }
                      >
                        {acc.clearance}
                      </span>
                    </div>
                    <div style={{ fontSize: 11, color: '#8298AE', marginTop: 2 }}>
                      {acc.command}
                    </div>
                    <div className="row between" style={{ marginTop: 6 }}>
                      <code
                        style={{
                          fontSize: 10.5,
                          fontFamily: 'var(--mono)',
                          color: '#D5A13C',
                        }}
                      >
                        {acc.email}
                      </code>
                      <span className="tiny" style={{ color: '#8298AE' }}>
                        Click to select
                      </span>
                    </div>
                  </div>
                ))}

                <div
                  style={{
                    fontSize: 10.5,
                    color: '#55687A',
                    marginTop: 6,
                    lineHeight: 1.4,
                  }}
                >
                  Shared demonstration password:{' '}
                  <code style={{ fontFamily: 'var(--mono)', color: '#8298AE' }}>Gotham@2026</code>
                  <br />
                  In operational deployment, shared credentials are not permitted and multi-factor
                  hardware tokens are enforced.
                </div>
              </div>
            )}
          </div>
        </form>
      </section>
    </div>
  )
}
