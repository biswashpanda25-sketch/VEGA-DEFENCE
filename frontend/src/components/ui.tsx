import React from 'react'

export function Card({ title, actions, children, bodyStyle, style }: {
  title?: React.ReactNode; actions?: React.ReactNode; children?: React.ReactNode
  bodyStyle?: React.CSSProperties; style?: React.CSSProperties
}) {
  return (
    <section className="card" style={style}>
      {(title || actions) && (
        <header className="card-h">
          <span className="card-t">{title}</span>
          <div className="row gap6">{actions}</div>
        </header>
      )}
      <div className="card-b" style={bodyStyle}>{children}</div>
    </section>
  )
}

export function KPI({ label, value, meta }: { label: string; value: React.ReactNode; meta?: string }) {
  return (
    <div className="card kpi">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {meta && <div className="kpi-meta">{meta}</div>}
    </div>
  )
}

const TONE: Record<string, string> = {
  confirmed: 'green', imported: 'blue', inferred: 'amber', unverified: 'red',
  active: 'green', degraded: 'amber', under_maintenance: 'amber', offline: 'red',
  low_stock: 'amber', in_progress: 'blue', open: 'blue', in_review: 'amber', closed: 'neutral',
  critical: 'red', warning: 'amber', info: 'blue', healthy: 'green', error: 'red',
  configured: 'neutral', pending: 'amber', approved: 'green', rejected: 'red',
  needs_revision: 'amber', evidence: 'teal', hypothesis: 'amber', assumption: 'blue', conclusion: 'accent',
}

export function Badge({ children, tone }: { children: React.ReactNode; tone?: string }) {
  const t = tone ?? TONE[String(children)] ?? 'neutral'
  return <span className={`badge ${t}`}>{children}</span>
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="empty row gap8" style={{ justifyContent: 'center' }}>
      <span className="spinner" /> {label ?? 'Loading…'}
    </div>
  )
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="empty">{children}</div>
}

export function ErrorBox({ error }: { error: unknown }) {
  const msg = error instanceof Error ? error.message : String(error)
  return <div className="banner crit">Request failed: {msg}</div>
}

export function SyntheticBanner() {
  return (
    <div className="banner warn" style={{ marginBottom: 14 }}>
      <span className="badge amber" style={{ flex: '0 0 auto' }}>SYNTHETIC DEMO</span>
      <span>All records in this workspace are simulated for demonstration. No classified, personal or operational data is present.</span>
    </div>
  )
}

export function Section({ title, sub, actions, children }: {
  title: string; sub?: string; actions?: React.ReactNode; children?: React.ReactNode
}) {
  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">{title}</h1>
          {sub && <div className="page-sub">{sub}</div>}
        </div>
        <div className="toolbar">{actions}</div>
      </div>
      {children}
    </>
  )
}
