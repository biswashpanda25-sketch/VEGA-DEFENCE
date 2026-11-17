import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, fmtDate, type EntityRow } from '../api'
import { Badge, Card, Empty, ErrorBox, Section, Spinner } from '../components/ui'
import { useUI } from '../store'

const TYPES = ['', 'organization', 'department', 'asset', 'vehicle', 'facility', 'warehouse',
  'inventory_item', 'project', 'document', 'case', 'location', 'supplier']

export default function Catalog() {
  const [q, setQ] = useState('')
  const [type, setType] = useState('')
  const [district, setDistrict] = useState('')
  const openPanel = useUI((s) => s.openPanel)

  const entities = useQuery({
    queryKey: ['catalog', type, district],
    queryFn: () => api.get<EntityRow[]>(`/entities?limit=300${type ? `&entity_type=${type}` : ''}${district ? `&district=${encodeURIComponent(district)}` : ''}`),
  })

  const rows = useMemo(() => {
    const list = entities.data ?? []
    if (!q.trim()) return list
    const t = q.toLowerCase()
    return list.filter((e) => e.name.toLowerCase().includes(t) || e.description.toLowerCase().includes(t) || e.district.toLowerCase().includes(t))
  }, [entities.data, q])

  const districts = useMemo(
    () => Array.from(new Set((entities.data ?? []).map((e) => e.district).filter(Boolean))).sort(),
    [entities.data],
  )

  async function inspect(id: string) {
    const detail = await api.get<any>(`/entities/${id}`)
    openPanel({
      kind: 'ENTITY RECORD',
      title: detail.entity.name,
      data: (
        <div className="stack gap8">
          <div className="row gap6" style={{ flexWrap: 'wrap' }}>
            <Badge tone="neutral">{detail.entity.entity_type}</Badge>
            <Badge>{detail.entity.status}</Badge>
            {detail.entity.is_synthetic && <Badge tone="amber">synthetic</Badge>}
          </div>
          <p className="tiny dim">{detail.entity.description || 'No description recorded.'}</p>
          <dl className="kv">
            <dt>District</dt><dd>{detail.entity.district || '—'}</dd>
            <dt>State</dt><dd>{detail.entity.state}</dd>
            <dt>Confidence</dt><dd>{(detail.entity.confidence * 100).toFixed(0)}%</dd>
            <dt>Record ID</dt><dd className="mono tiny" style={{ wordBreak: 'break-all' }}>{detail.entity.id}</dd>
          </dl>
          <div className="eyebrow" style={{ marginTop: 6 }}>Provenance</div>
          <pre className="mono tiny muted" style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
            {JSON.stringify(detail.entity.attributes, null, 2)}
          </pre>
          <div className="eyebrow" style={{ marginTop: 6 }}>Relationships ({detail.relationships.length})</div>
          {detail.relationships.slice(0, 8).map((r: any) => (
            <div key={r.id} className="evidence">
              <div className="row gap6" style={{ flexWrap: 'wrap' }}>
                <Badge>{r.provenance}</Badge>
                <span className="tiny mono">{r.rel_type}</span>
              </div>
              <div className="tiny" style={{ marginTop: 3 }}>{r.source_name} → {r.target_name}</div>
              <div className="tiny muted" style={{ marginTop: 2 }}>{r.evidence}</div>
            </div>
          ))}
        </div>
      ),
    })
  }

  return (
    <Section
      title="Data Catalog"
      sub="Canonical entity records across all authorized sources, with provenance and quality metadata."
      actions={<span className="tiny muted">{rows.length} of {entities.data?.length ?? 0} records</span>}
    >
      <div className="toolbar" style={{ marginBottom: 12 }}>
        <div className="searchbox"><input className="input" placeholder="Filter by name, description or district…" value={q} onChange={(e) => setQ(e.target.value)} /></div>
        <select className="input" style={{ width: 170 }} value={type} onChange={(e) => setType(e.target.value)} aria-label="Entity type">
          {TYPES.map((t) => <option key={t} value={t}>{t ? t.replace(/_/g, ' ') : 'All types'}</option>)}
        </select>
        <select className="input" style={{ width: 160 }} value={district} onChange={(e) => setDistrict(e.target.value)} aria-label="District">
          <option value="">All districts</option>
          {districts.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
      </div>

      {entities.error && <ErrorBox error={entities.error} />}
      <Card bodyStyle={{ padding: 0 }}>
        {entities.isLoading ? <Spinner /> : (
          <div className="tbl-wrap">
            <table>
              <thead>
                <tr><th>Name</th><th>Type</th><th>District</th><th>Status</th><th>Confidence</th><th>Provenance</th><th></th></tr>
              </thead>
              <tbody>
                {rows.map((e) => (
                  <tr key={e.id}>
                    <td>{e.name}</td>
                    <td><span className="tiny mono dim">{e.entity_type}</span></td>
                    <td>{e.district || <span className="muted">—</span>}</td>
                    <td><Badge>{e.status}</Badge></td>
                    <td className="mono tiny">{(e.confidence * 100).toFixed(0)}%</td>
                    <td>{e.is_synthetic ? <Badge tone="amber">synthetic</Badge> : <Badge tone="blue">imported</Badge>}</td>
                    <td style={{ textAlign: 'right' }}>
                      <button className="btn sm ghost" onClick={() => inspect(e.id)}>Inspect</button>
                    </td>
                  </tr>
                ))}
                {rows.length === 0 && <tr><td colSpan={7}><Empty>No records match the current filters</Empty></td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      <div className="tiny muted" style={{ marginTop: 8 }}>
        Catalog views are permission-filtered server-side: records from other organizations are never returned.
        Last refreshed {fmtDate(new Date().toISOString())}.
      </div>
    </Section>
  )
}
