import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api, fmtDate, type Overview } from '../api'
import { Card, ErrorBox, KPI, Spinner, Badge, Section, SyntheticBanner } from '../components/ui'
import { EChart, barOption, donutOption } from '../components/charts'

export default function Overview_Page() {
  const ov = useQuery({ queryKey: ['overview'], queryFn: () => api.get<Overview>('/analytics/overview') })
  const notifs = useQuery({ queryKey: ['notif-overview'], queryFn: () => api.get<any[]>('/notifications') })
  const cases = useQuery({ queryKey: ['cases-overview'], queryFn: () => api.get<any[]>('/cases') })
  const health = useQuery({ queryKey: ['asset-health'], queryFn: () => api.get<any>('/analytics/asset-health') })

  if (ov.isLoading) return <Spinner />
  if (ov.error) return <ErrorBox error={ov.error} />
  const d = ov.data!

  return (
    <Section title="Operational Overview" sub="Current state of the authorized information environment, scoped to your organization and role.">
      <SyntheticBanner />

      <div className="grid g4" style={{ marginBottom: 12 }}>
        <KPI label="Tracked entities" value={d.entities} meta={`${Object.keys(d.entities_by_type).length} entity types`} />
        <KPI label="Relationships" value={d.relationships} meta={`${d.relationships_by_provenance?.inferred ?? 0} inferred · requiring review`} />
        <KPI label="Analytical cases" value={d.cases} meta={`${d.open_cases} open`} />
        <KPI label="Datasets / documents" value={`${d.datasets} / ${d.documents}`} meta="Ingested synthetic sources" />
      </div>

      <div className="grid g-2-1" style={{ marginBottom: 12 }}>
        <Card title="Entity distribution by type" actions={<span className="tiny muted">live query</span>}>
          {Object.keys(d.entities_by_type).length
            ? <EChart option={barOption(d.entities_by_type, true)} height={240} />
            : <div className="empty">No entities ingested yet</div>}
        </Card>
        <Card title="Relationship provenance">
          <EChart option={donutOption(d.relationships_by_provenance ?? {})} height={240} />
          <div className="tiny muted" style={{ marginTop: 8 }}>
            Inferred links are hypotheses, not established facts. Each relationship carries source evidence.
          </div>
        </Card>
      </div>

      <div className="grid g3" style={{ marginBottom: 12 }}>
        <Card title="Asset availability" actions={<Badge tone="neutral">derived</Badge>}>
          {health.isLoading ? <Spinner /> : health.data && (
            <>
              <div className="row between" style={{ marginBottom: 8 }}>
                <span className="kpi-value" style={{ fontSize: 20 }}>{(health.data.availability_ratio * 100).toFixed(1)}%</span>
                <span className="tiny muted">record-based ratio</span>
              </div>
              <div className="kv">
                <dt>Tracked</dt><dd>{health.data.tracked_assets}</dd>
                <dt>Operational</dt><dd>{health.data.operational}</dd>
                <dt>Degraded</dt><dd>{health.data.degraded}</dd>
                <dt>Offline</dt><dd>{health.data.offline}</dd>
              </div>
              <div className="tiny muted" style={{ marginTop: 8 }}>{health.data.limitations}</div>
            </>
          )}
        </Card>

        <Card title="Active cases" actions={<Link to="/cases" className="tiny muted">Open workspace →</Link>}>
          {(cases.data ?? []).length === 0 && <div className="empty">No cases</div>}
          {(cases.data ?? []).slice(0, 4).map((c) => (
            <div key={c.id} style={{ padding: '7px 0', borderBottom: '1px solid var(--line)' }}>
              <div className="row between gap8">
                <Link to="/cases" style={{ fontSize: 12 }}>{c.title}</Link>
                <Badge>{c.status}</Badge>
              </div>
              <div className="tiny muted">{c.classification} · {c.created_by}</div>
            </div>
          ))}
        </Card>

        <Card title="Notifications" actions={<Link to="/notifications" className="tiny muted">All →</Link>}>
          {(notifs.data ?? []).length === 0 && <div className="empty">Nothing to report</div>}
          {(notifs.data ?? []).slice(0, 4).map((n) => (
            <div key={n.id} style={{ padding: '7px 0', borderBottom: '1px solid var(--line)' }}>
              <div className="row between gap8">
                <span style={{ fontSize: 12 }}>{n.title}</span>
                <Badge>{n.severity}</Badge>
              </div>
              <div className="tiny muted">{fmtDate(n.created_at)}</div>
            </div>
          ))}
        </Card>
      </div>

      <Card title="Data basis and limitations">
        <div className="grid g2">
          <div className="stack gap8">
            <div className="tiny dim">{d.data_basis}</div>
            <div className="tiny muted">
              Counts are computed from the platform database at request time and filtered by your organization.
              Platform administrators see all tenants aggregated.
            </div>
          </div>
          <div className="stack gap8">
            <div className="row between"><span className="tiny muted">Synthetic data</span><Badge tone="amber">100%</Badge></div>
            <div className="row between"><span className="tiny muted">Live external integrations</span><Badge tone="red">none configured</Badge></div>
            <div className="row between"><span className="tiny muted">Geospatial anchoring</span><Badge tone="blue">district approximations</Badge></div>
          </div>
        </div>
      </Card>
    </Section>
  )
}
