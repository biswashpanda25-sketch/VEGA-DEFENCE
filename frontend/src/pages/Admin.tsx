import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, fmtDate, roleLabel, ROLES } from '../api'
import { Badge, Card, Empty, ErrorBox, KPI, Section, Spinner } from '../components/ui'
import { EChart, barOption } from '../components/charts'
import { useAuth, useUI } from '../store'

export default function Admin({
  defaultTab = 'users',
  showOrgsOnly = false,
}: {
  defaultTab?: 'users' | 'system' | 'ai'
  showOrgsOnly?: boolean
}) {
  const user = useAuth((s) => s.user)
  const qc = useQueryClient()
  const notify = useUI((s) => s.notify)
  const [tab, setTab] = useState<'users' | 'system' | 'ai'>(defaultTab)

  const isAdmin = ['platform_admin', 'org_admin'].includes(user?.role ?? '')
  const users = useQuery({ queryKey: ['admin-users'], queryFn: () => api.get<any[]>('/admin/users'), retry: 0 })
  const health = useQuery({ queryKey: ['system-health'], queryFn: () => api.get<any>('/admin/system-health') })
  const usage = useQuery({ queryKey: ['ai-usage'], queryFn: () => api.get<any>('/admin/ai-usage'), retry: 0 })
  const connectors = useQuery({ queryKey: ['connectors'], queryFn: () => api.get<any[]>('/admin/connectors'), retry: 0 })
  const orgs = useQuery({ queryKey: ['orgs'], queryFn: () => api.get<any[]>('/organizations') })

  const setRole = useMutation({
    mutationFn: ({ id, role }: { id: string; role: string }) => api.patch<any>(`/admin/users/${id}/role?role=${role}`),
    onSuccess: () => { notify('Role updated and audited'); qc.invalidateQueries({ queryKey: ['admin-users'] }) },
  })

  if (showOrgsOnly) {
    return (
      <Card title="Command &amp; Organisation Registry (Tenants)">
        <div className="tbl-wrap">
          <table>
            <thead>
              <tr>
                <th>Command / Organisation</th>
                <th>Code</th>
                <th>Type</th>
                <th>Jurisdiction / State</th>
              </tr>
            </thead>
            <tbody>
              {(orgs.data ?? []).map((o) => (
                <tr key={o.id}>
                  <td style={{ fontWeight: 500 }}>{o.name}</td>
                  <td className="mono tiny">{o.code}</td>
                  <td><Badge tone="neutral">{o.type}</Badge></td>
                  <td>{o.state}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="tiny muted" style={{ marginTop: 10 }}>
          Tenant isolation is enforced strictly at the database query layer.
        </div>
      </Card>
    )
  }

  return (
    <Section title="Administration" sub="Identity, connector health, model configuration and system posture. Every administrative action is audited.">
      <div className="tabs">
        <button className={`tab${tab === 'users' ? ' active' : ''}`} onClick={() => setTab('users')}>Users &amp; roles</button>
        <button className={`tab${tab === 'system' ? ' active' : ''}`} onClick={() => setTab('system')}>System &amp; connectors</button>
        <button className={`tab${tab === 'ai' ? ' active' : ''}`} onClick={() => setTab('ai')}>AI governance</button>
      </div>

      {tab === 'users' && (
        <div className="stack gap12">
          {!isAdmin && <div className="banner warn">User administration requires organization or platform administrator privileges.</div>}
          {users.error && <ErrorBox error={users.error} />}
          {isAdmin && (
            <Card title="Organization users" bodyStyle={{ padding: 0 }} actions={<span className="tiny muted">{users.data?.length ?? 0}</span>}>
              {users.isLoading ? <Spinner /> : (
                <div className="tbl-wrap">
                  <table>
                    <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Last login</th></tr></thead>
                    <tbody>
                      {(users.data ?? []).map((u) => (
                        <tr key={u.id}>
                          <td>{u.full_name}</td>
                          <td className="tiny mono dim">{u.email}</td>
                          <td>
                            <select className="input" style={{ width: 140, padding: '3px 6px', fontSize: 11 }}
                              value={u.role} onChange={(e) => setRole.mutate({ id: u.id, role: e.target.value })}>
                              {ROLES.map((r) => <option key={r} value={r}>{roleLabel(r)}</option>)}
                            </select>
                          </td>
                          <td><Badge tone={u.is_active ? 'green' : 'red'}>{u.is_active ? 'active' : 'disabled'}</Badge></td>
                          <td className="tiny muted">{fmtDate(u.last_login_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {setRole.error && <div style={{ padding: 12 }}><ErrorBox error={setRole.error} /></div>}
            </Card>
          )}

          <Card title="Organizations (tenants)">
            <div className="tbl-wrap">
              <table>
                <thead><tr><th>Name</th><th>Code</th><th>Type</th><th>State</th></tr></thead>
                <tbody>
                  {(orgs.data ?? []).map((o) => (
                    <tr key={o.id}><td>{o.name}</td><td className="mono tiny">{o.code}</td><td>{o.type}</td><td>{o.state}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="tiny muted" style={{ marginTop: 8 }}>
              Non-platform administrators see only their own organization. Cross-tenant access is refused at the query layer.
            </div>
          </Card>
        </div>
      )}

      {tab === 'system' && (
        <div className="stack gap12">
          <div className="grid g4">
            <KPI label="API" value={health.data?.api ?? '—'} meta={health.data?.runtime} />
            <KPI label="Database" value={health.data?.database ?? '—'} meta="connectivity probe" />
            <KPI label="Users" value={health.data?.counts?.users ?? '—'} meta="all organizations" />
            <KPI label="Entities" value={health.data?.counts?.entities ?? '—'} meta="all organizations" />
          </div>
          <Card title="Connector health" bodyStyle={{ padding: 0 }}>
            {connectors.error ? <Empty>Requires data-admin or higher</Empty> : connectors.isLoading ? <Spinner /> : (
              <table>
                <thead><tr><th>Connector</th><th>Kind</th><th>Status</th><th>Last run</th><th>Error</th></tr></thead>
                <tbody>
                  {(connectors.data ?? []).map((c) => (
                    <tr key={c.id}>
                      <td>{c.name}</td><td><Badge tone="neutral">{c.kind}</Badge></td>
                      <td><Badge>{c.status}</Badge></td>
                      <td className="tiny muted">{fmtDate(c.last_run_at)}</td>
                      <td className="tiny muted">{c.last_error ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>
          <Card title="Storage & capacity">
            <div className="banner">
              Storage monitoring, backup scheduling and restore drills are defined in the operational runbook
              (docs/OPERATIONS.md). In this sandbox the primary store is a local SQLite file; production targets
              PostgreSQL with PostGIS and pgvector, with object storage for documents.
            </div>
          </Card>
        </div>
      )}

      {tab === 'ai' && (
        <div className="stack gap12">
          {usage.error && <ErrorBox error={usage.error} />}
          <div className="grid g4">
            <KPI label="AI queries" value={usage.data?.queries ?? '—'} meta="logged with citations" />
            <KPI label="Citation coverage" value={`${((usage.data?.citation_coverage ?? 0) * 100).toFixed(0)}%`} meta="queries with ≥1 citation" />
            <KPI label="Provider" value={health.data?.ai_provider ?? '—'} meta="model abstraction layer" />
            <KPI label="Prompt version" value="v1" meta="versioned system policy" />
          </div>
          <div className="grid g2">
            <Card title="AI governance controls">
              <div className="stack gap8 tiny muted">
                <div>• Retrieval is permission-filtered before generation.</div>
                <div>• Model output is rejected unless every citation resolves to a retrieved record.</div>
                <div>• Prompt-injection defence: retrieved text is never treated as instructions.</div>
                <div>• No autonomous permission changes or workflow execution.</div>
                <div>• Human approval required for consequential actions.</div>
              </div>
            </Card>
            <Card title="Evaluation status">
              <div className="tiny muted" style={{ marginBottom: 8 }}>
                Offline evaluation harness measures groundedness and citation correctness on a labelled synthetic set.
                Run: <code className="mono">python -m tests.eval_ai</code>
              </div>
              <div className="banner warn">
                No benchmark figures are displayed here unless measured by the harness in this environment. See
                docs/EVALUATION.md for the executed results.
              </div>
            </Card>
          </div>
        </div>
      )}
    </Section>
  )
}
