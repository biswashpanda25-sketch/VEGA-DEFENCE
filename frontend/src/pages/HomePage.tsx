import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api, fmtDate, type EntityRow, type Overview } from '../api'
import { Card, Empty, ErrorBox, KPI, Section, Spinner, SyntheticBanner, Badge } from '../components/ui'
import { EChart, barOption, donutOption, palette } from '../components/charts'
import { IcAI, IcCase, IcMap, IcPlus, IcSource } from '../components/icons'
import { useUI } from '../store'

export default function HomePage() {
  const [params, setParams] = useSearchParams()
  const activeTab = params.get('tab') || 'overview'
  const nav = useNavigate()
  const openPanel = useUI((s) => s.openPanel)
  const [showInsights, setShowInsights] = useState(false)

  const ov = useQuery({ queryKey: ['overview'], queryFn: () => api.get<Overview>('/analytics/overview') })
  const notifs = useQuery({ queryKey: ['notifications'], queryFn: () => api.get<any[]>('/notifications') })
  const cases = useQuery({ queryKey: ['cases'], queryFn: () => api.get<any[]>('/cases') })
  const health = useQuery({ queryKey: ['asset-health'], queryFn: () => api.get<any>('/analytics/asset-health') })
  const entities = useQuery({ queryKey: ['home-entities'], queryFn: () => api.get<EntityRow[]>('/entities?limit=200') })

  if (ov.isLoading || notifs.isLoading || cases.isLoading || health.isLoading) {
    return <Spinner label="Loading operational intelligence workspace…" />
  }

  if (ov.error) return <ErrorBox error={ov.error} />

  const d = ov.data!
  const h = health.data
  const allNotifications = notifs.data ?? []
  const allCases = cases.data ?? []
  const opsEntities = (entities.data ?? []).filter((e) =>
    ['asset', 'vehicle', 'facility', 'warehouse', 'inventory_item'].includes(e.entity_type)
  )
  const exceptions = opsEntities.filter((e) => !['active', 'in_progress'].includes(e.status))

  return (
    <Section
      title="Home"
      sub="Your authorised institutional intelligence workspace. Review priorities, launch investigations, and query records."
      actions={
        <div className="row gap8">
          <button className="btn primary" onClick={() => nav('/ask')}>
            <IcAI size={14} /> Ask VEGA
          </button>
          <button className="btn" onClick={() => nav('/data?tab=add')}>
            <IcSource size={14} /> Add Data
          </button>
          <button className="btn" onClick={() => nav('/investigations?create=true')}>
            <IcPlus size={14} /> New Investigation
          </button>
        </div>
      }
    >
      <SyntheticBanner />

      {/* Tabs for Overview, Activity stream, and Operational posture */}
      <div className="tabs">
        <button
          className={`tab${activeTab === 'overview' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'overview' })}
        >
          Intelligent Overview
        </button>
        <button
          className={`tab${activeTab === 'activity' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'activity' })}
        >
          Activity &amp; Alerts ({allNotifications.filter((n) => !n.is_read).length} unread)
        </button>
        <button
          className={`tab${activeTab === 'operations' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'operations' })}
        >
          Operational Posture ({exceptions.length} exceptions)
        </button>
      </div>

      {activeTab === 'overview' && (
        <div className="stack gap12">
          {/* Welcome & Primary Actions */}
          <div className="grid g4">
            <div
              className="card"
              style={{
                cursor: 'pointer',
                padding: '16px',
                borderLeft: '3px solid var(--accent)',
                transition: 'transform 0.1s ease',
              }}
              onClick={() => nav('/ask')}
            >
              <div className="row between">
                <span className="eyebrow">Intelligence Co-Pilot</span>
                <IcAI size={18} />
              </div>
              <div style={{ fontSize: 15, fontWeight: 600, marginTop: 8 }}>Ask VEGA</div>
              <div className="tiny muted" style={{ marginTop: 4 }}>
                Natural-language Q&amp;A grounded in authorized records and citations.
              </div>
            </div>

            <div
              className="card"
              style={{
                cursor: 'pointer',
                padding: '16px',
                borderLeft: '3px solid var(--blue)',
                transition: 'transform 0.1s ease',
              }}
              onClick={() => nav('/data?tab=add')}
            >
              <div className="row between">
                <span className="eyebrow">Information Ingest</span>
                <IcSource size={18} />
              </div>
              <div style={{ fontSize: 15, fontWeight: 600, marginTop: 8 }}>Add Data</div>
              <div className="tiny muted" style={{ marginTop: 4 }}>
                Guided 4-step wizard for CSV, Excel, and JSON records.
              </div>
            </div>

            <div
              className="card"
              style={{
                cursor: 'pointer',
                padding: '16px',
                borderLeft: '3px solid var(--teal)',
                transition: 'transform 0.1s ease',
              }}
              onClick={() => nav('/explore')}
            >
              <div className="row between">
                <span className="eyebrow">Analytical Workspace</span>
                <IcMap size={18} />
              </div>
              <div style={{ fontSize: 15, fontWeight: 600, marginTop: 8 }}>Explore Information</div>
              <div className="tiny muted" style={{ marginTop: 4 }}>
                Unified geospatial map, knowledge connections, and timeline.
              </div>
            </div>

            <div
              className="card"
              style={{
                cursor: 'pointer',
                padding: '16px',
                borderLeft: '3px solid var(--amber)',
                transition: 'transform 0.1s ease',
              }}
              onClick={() => nav('/investigations')}
            >
              <div className="row between">
                <span className="eyebrow">Evidence &amp; Review</span>
                <IcCase size={18} />
              </div>
              <div style={{ fontSize: 15, fontWeight: 600, marginTop: 8 }}>Active Investigations</div>
              <div className="tiny muted" style={{ marginTop: 4 }}>
                {allCases.length} case files under review with SITREP export.
              </div>
            </div>
          </div>

          {/* Priority items needing action & Recent Activity */}
          <div className="grid g-2-1">
            <Card
              title="Items Requiring Attention"
              actions={<Badge tone="amber">{exceptions.length + allNotifications.filter(n => n.severity === 'warning').length} active</Badge>}
            >
              <div className="stack gap8">
                {exceptions.slice(0, 4).map((ex) => (
                  <div
                    key={ex.id}
                    className="row between"
                    style={{
                      padding: '8px 10px',
                      background: 'var(--panel-2)',
                      borderRadius: 3,
                      border: '1px solid var(--line)',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 12.5, fontWeight: 600 }}>{ex.name}</div>
                      <div className="tiny muted">
                        {ex.district} · {ex.entity_type} · Status:{' '}
                        <Badge>{ex.status}</Badge>
                      </div>
                    </div>
                    <button
                      className="btn sm ghost"
                      onClick={() => nav(`/explore?tab=connections&node=${ex.id}`)}
                    >
                      Inspect in Explore
                    </button>
                  </div>
                ))}
                {allNotifications.filter((n) => !n.is_read).slice(0, 2).map((n) => (
                  <div
                    key={n.id}
                    className="row between"
                    style={{
                      padding: '8px 10px',
                      background: 'rgba(217,119,6,0.06)',
                      borderRadius: 3,
                      border: '1px solid rgba(217,119,6,0.2)',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 12.5, fontWeight: 600 }}>{n.title}</div>
                      <div className="tiny muted">{n.message}</div>
                    </div>
                    <Badge tone={n.severity}>{n.severity}</Badge>
                  </div>
                ))}
                {exceptions.length === 0 && (
                  <Empty>All monitored records and posture indicators are operational.</Empty>
                )}
              </div>
            </Card>

            <Card
              title="Active Investigations"
              actions={
                <Link to="/investigations" className="tiny muted">
                  View all ({allCases.length})
                </Link>
              }
            >
              <div className="stack gap8">
                {allCases.slice(0, 3).map((c) => (
                  <div
                    key={c.id}
                    style={{
                      padding: '9px 11px',
                      border: '1px solid var(--line)',
                      borderRadius: 3,
                    }}
                  >
                    <div className="row between">
                      <span style={{ fontSize: 12.5, fontWeight: 600 }}>{c.title}</span>
                      <Badge tone={c.status === 'in_review' ? 'amber' : 'blue'}>{c.status}</Badge>
                    </div>
                    <div className="tiny muted" style={{ marginTop: 3 }}>
                      Officer: {c.created_by} · Classification: {c.classification}
                    </div>
                    <div className="row gap6" style={{ marginTop: 6 }}>
                      <button
                        className="btn sm ghost"
                        onClick={() => nav(`/investigations?caseId=${c.id}`)}
                      >
                        Open dossier
                      </button>
                    </div>
                  </div>
                ))}
                {allCases.length === 0 && <Empty>No active investigations</Empty>}
              </div>
            </Card>
          </div>

          {/* Progressive Disclosure: Collapsible System Insights */}
          <Card
            title="System Insights &amp; Record Telemetry"
            actions={
              <button
                className="btn sm ghost"
                onClick={() => setShowInsights((v) => !v)}
              >
                {showInsights ? 'Collapse Insights' : 'Expand Detailed Metrics'}
              </button>
            }
          >
            {showInsights ? (
              <div className="stack gap12" style={{ marginTop: 4 }}>
                <div className="grid g4">
                  <KPI
                    label="Tracked entities"
                    value={d.entities}
                    meta={`${Object.keys(d.entities_by_type).length} entity types`}
                  />
                  <KPI
                    label="Relationships"
                    value={d.relationships}
                    meta={`${d.relationships_by_provenance?.inferred ?? 0} inferred · requiring review`}
                  />
                  <KPI
                    label="Availability ratio"
                    value={`${(h.availability_ratio * 100).toFixed(1)}%`}
                    meta={`${h.operational} of ${h.tracked_assets} operational`}
                  />
                  <KPI
                    label="Datasets / documents"
                    value={`${d.datasets} / ${d.documents}`}
                    meta="Ingested synthetic sources"
                  />
                </div>

                <div className="grid g2">
                  <div>
                    <div className="eyebrow" style={{ marginBottom: 6 }}>
                      Entity distribution by type
                    </div>
                    <EChart option={barOption(d.entities_by_type, true)} height={210} />
                  </div>
                  <div>
                    <div className="eyebrow" style={{ marginBottom: 6 }}>
                      Relationship provenance
                    </div>
                    <EChart option={donutOption(d.relationships_by_provenance ?? {})} height={210} />
                    <div className="tiny muted" style={{ marginTop: 6 }}>
                      Inferred links represent working hypotheses and require reviewer corroboration.
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="row between" style={{ color: 'var(--text-3)', fontSize: 12 }}>
                <span>
                  {d.entities} entities across {Object.keys(d.entities_by_type).length} types · {d.relationships} links · {(h.availability_ratio * 100).toFixed(0)}% posture
                </span>
                <span className="tiny font-medium">Click Expand to view charts and breakdown</span>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Activity & Alerts Tab */}
      {activeTab === 'activity' && (
        <div className="grid g-2-1">
          <Card
            title="Notification Stream &amp; Operational Events"
            actions={<span className="tiny muted">{allNotifications.length} total events</span>}
          >
            <div className="stack gap8">
              {allNotifications.map((n) => (
                <div
                  key={n.id}
                  style={{
                    padding: '10px 12px',
                    border: '1px solid var(--line)',
                    borderRadius: 3,
                    background: n.is_read ? 'transparent' : 'rgba(217,119,6,0.04)',
                    borderLeft: `3px solid ${n.severity === 'warning' ? 'var(--amber)' : 'var(--blue)'}`,
                  }}
                >
                  <div className="row between gap8">
                    <span style={{ fontSize: 12.5, fontWeight: 600 }}>{n.title}</span>
                    <Badge tone={n.severity}>{n.severity}</Badge>
                  </div>
                  <div className="tiny dim" style={{ marginTop: 3 }}>
                    {n.message}
                  </div>
                  <div className="tiny muted" style={{ marginTop: 4 }}>
                    {fmtDate(n.created_at)}
                  </div>
                </div>
              ))}
              {allNotifications.length === 0 && <Empty>No active notifications</Empty>}
            </div>
          </Card>

          <Card title="Activity Context">
            <div className="stack gap8 tiny muted">
              <div>
                <strong>Notifications</strong> are generated automatically from ingestion pipelines,
                clearance changes, and operational status updates.
              </div>
              <div className="hr" />
              <div>
                <strong>Institutional channels</strong> (Email, Webhook) require verified sovereign
                credentials; in this demonstration build, in-application delivery is active.
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Operational Posture Tab */}
      {activeTab === 'operations' && (
        <div className="stack gap12">
          <div className="grid g4">
            <KPI label="Tracked operational items" value={h.tracked_assets} meta="bases, radar, depots, crossings" />
            <KPI label="Availability ratio" value={`${(h.availability_ratio * 100).toFixed(0)}%`} meta="recorded status basis" />
            <KPI label="Exceptions needing action" value={exceptions.length} meta="degraded, under maintenance, low stock" />
            <KPI label="Forecast horizon" value="3 months" meta="simple trend projection" />
          </div>

          <Card title="Maintenance and Exception Queue" bodyStyle={{ padding: 0 }}>
            {exceptions.length === 0 ? (
              <Empty>No maintenance exceptions recorded</Empty>
            ) : (
              <div className="tbl-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Installation / Asset</th>
                      <th>Type</th>
                      <th>District / Sector</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {exceptions.map((e) => (
                      <tr key={e.id}>
                        <td style={{ fontWeight: 500 }}>{e.name}</td>
                        <td><Badge tone="neutral">{e.entity_type}</Badge></td>
                        <td>{e.district || '—'}</td>
                        <td><Badge tone={e.status}>{e.status}</Badge></td>
                        <td>
                          <button
                            className="btn sm ghost"
                            onClick={() => nav(`/explore?tab=connections&node=${e.id}`)}
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      )}
    </Section>
  )
}
