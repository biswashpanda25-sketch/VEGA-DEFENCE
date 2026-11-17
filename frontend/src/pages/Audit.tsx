import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, fmtDate } from '../api'
import { Badge, Card, Empty, ErrorBox, KPI, Section, Spinner } from '../components/ui'
import { EChart, barOption } from '../components/charts'

const ACTION_GROUPS: Record<string, string> = {
  auth: 'Authentication', dataset: 'Data ingestion', entity: 'Entities', relationship: 'Relationships',
  case: 'Cases', finding: 'Findings', search: 'Search', ai: 'AI assistance', admin: 'Administration',
}

export default function Audit() {
  const [filter, setFilter] = useState('')
  const log = useQuery({
    queryKey: ['audit', filter],
    queryFn: () => api.get<any[]>(`/audit?limit=300${filter ? `&action=${filter}` : ''}`),
    retry: 0,
  })

  const counts = useMemo(() => {
    const c: Record<string, number> = {}
    ;(log.data ?? []).forEach((e) => {
      const grp = e.action.split('.')[0]
      c[grp] = (c[grp] ?? 0) + 1
    })
    return c
  }, [log.data])

  if (log.error) {
    return (
      <Section title="Security & Audit" sub="Tamper-evident activity log.">
        <div className="banner warn">
          Audit access requires auditor, organization administrator or platform administrator privileges.
          Your current role does not include audit read access — this restriction is itself recorded.
        </div>
      </Section>
    )
  }

  return (
    <Section
      title="Security & Audit"
      sub="Authentication, access, modification and AI activity recorded server-side. Entries are append-only and organization-scoped."
      actions={<span className="badge neutral">{(log.data ?? []).length} events</span>}
    >
      <div className="grid g4" style={{ marginBottom: 12 }}>
        {Object.entries(ACTION_GROUPS).slice(0, 4).map(([k, label]) => (
          <KPI key={k} label={label} value={counts[k] ?? 0} meta="events in window" />
        ))}
      </div>

      <div className="grid g-2-1">
        <Card title="Event stream" bodyStyle={{ padding: 0 }} actions={
          <select className="input" style={{ width: 170, padding: '3px 6px', fontSize: 11 }} value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="">All actions</option>
            {Object.keys(ACTION_GROUPS).map((g) => <option key={g} value={g}>{ACTION_GROUPS[g]}</option>)}
          </select>
        }>
          {log.isLoading ? <Spinner /> : (
            <div className="tbl-wrap" style={{ maxHeight: 520 }}>
              <table>
                <thead><tr><th>Time (IST)</th><th>Action</th><th>Detail</th><th>Resource</th></tr></thead>
                <tbody>
                  {(log.data ?? []).map((e) => (
                    <tr key={e.id}>
                      <td className="tiny mono muted" style={{ whiteSpace: 'nowrap' }}>{fmtDate(e.created_at)}</td>
                      <td><Badge tone={e.action.startsWith('auth') ? 'blue' : e.action.startsWith('admin') ? 'amber' : 'neutral'}>{e.action}</Badge></td>
                      <td className="tiny">{e.detail}</td>
                      <td className="tiny mono muted">{String(e.resource ?? '').slice(0, 12)}</td>
                    </tr>
                  ))}
                  {(log.data ?? []).length === 0 && <tr><td colSpan={4}><Empty>No events</Empty></td></tr>}
                </tbody>
              </table>
            </div>
          )}
        </Card>
        <div className="stack gap12">
          <Card title="Activity by domain">
            <EChart option={barOption(counts, true)} height={230} />
          </Card>
          <Card title="Retention and integrity">
            <div className="stack gap8 tiny muted">
              <div>• Events are append-only; the API exposes no update or delete route.</div>
              <div>• Demonstration retention: 90 days. Production retention is organization-configurable.</div>
              <div>• Secrets, passwords and tokens are never written to the audit detail field.</div>
              <div>• Production hardening: hash-chained audit rows plus write-once object storage export.</div>
            </div>
          </Card>
        </div>
      </div>
    </Section>
  )
}
