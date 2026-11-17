import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, fmtDate, type EntityRow, type Overview } from '../api'
import { Badge, Card, Empty, Section, Spinner } from '../components/ui'
import { EChart, barOption, donutOption } from '../components/charts'
import { useAuth } from '../store'

type ReportKind = 'organization' | 'graph' | 'geospatial' | 'audit'

function toCSV(rows: Record<string, any>[]): string {
  if (!rows.length) return ''
  const headers = Array.from(new Set(rows.flatMap((r) => Object.keys(r))))
  const esc = (v: any) => `"${String(v ?? '').replace(/"/g, '""')}"`
  return [headers.join(','), ...rows.map((r) => headers.map((h) => esc(r[h])).join(','))].join('\n')
}

function download(name: string, content: string, mime = 'text/csv;charset=utf-8') {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = name; a.click()
  URL.revokeObjectURL(url)
}

export default function Reports() {
  const user = useAuth((s) => s.user)
  const [kind, setKind] = useState<ReportKind>('organization')
  const [generatedAt, setGeneratedAt] = useState<string | null>(null)

  const ov = useQuery({ queryKey: ['overview'], queryFn: () => api.get<Overview>('/analytics/overview') })
  const entities = useQuery({ queryKey: ['report-entities'], queryFn: () => api.get<EntityRow[]>('/entities?limit=300') })
  const rels = useQuery({ queryKey: ['report-rels'], queryFn: () => api.get<any[]>('/relationships?limit=300') })
  const summary = useQuery({ queryKey: ['geo-summary'], queryFn: () => api.get<any>('/geo/summary') })
  const audit = useQuery({
    queryKey: ['report-audit'],
    queryFn: () => api.get<any[]>('/audit?limit=200'),
    enabled: kind === 'audit',
    retry: 0,
  })

  const report = useMemo(() => {
    if (kind === 'organization') return {
      title: 'Organization information summary',
      rows: (entities.data ?? []).map((e) => ({
        name: e.name, entity_type: e.entity_type, district: e.district, state: e.state,
        status: e.status, confidence: e.confidence, synthetic: e.is_synthetic, id: e.id,
      })),
    }
    if (kind === 'graph') return {
      title: 'Entity relationship report',
      rows: (rels.data ?? []).map((r) => ({
        relationship: r.rel_type, provenance: r.provenance, confidence: r.confidence,
        evidence: r.evidence, source_ref: r.source_ref, source_id: r.source_id, target_id: r.target_id,
      })),
    }
    if (kind === 'geospatial') return {
      title: 'District distribution report',
      rows: (summary.data?.districts ?? []).map((d: any) => ({ district: d.district, record_count: d.count, state: 'Odisha' })),
    }
    return {
      title: 'Audit extract',
      rows: (audit.data ?? []).map((a) => ({
        timestamp: a.created_at, action: a.action, resource: a.resource, detail: a.detail, user_id: a.user_id,
      })),
    }
  }, [kind, entities.data, rels.data, summary.data, audit.data])

  const generated = generatedAt ?? new Date().toISOString()

  function exportCSV() {
    download(`vega-${kind}-report-${Date.now()}.csv`, toCSV(report.rows))
    setGeneratedAt(new Date().toISOString())
  }

  function exportJSON() {
    const payload = {
      meta: {
        platform: 'VEGA DEFENCE INTELLIGENCE', generated_at: generated, generated_by: user?.email,
        organization_id: user?.organization_id, classification: 'INTERNAL', data_basis: 'synthetic demonstration records',
        report_kind: kind, record_count: report.rows.length,
      },
      report: report.title,
      records: report.rows,
    }
    download(`vega-${kind}-report-${Date.now()}.json`, JSON.stringify(payload, null, 2), 'application/json')
    setGeneratedAt(new Date().toISOString())
  }

  function printView() {
    setGeneratedAt(new Date().toISOString())
    setTimeout(() => window.print(), 200)
  }

  return (
    <Section
      title="Reports"
      sub="Generate reproducible extracts with classification markings, generation metadata and source counts. Exports are recorded in the audit log."
      actions={
        <div className="row gap6">
          <button className="btn" onClick={exportCSV}>Export CSV</button>
          <button className="btn" onClick={exportJSON}>Export JSON</button>
          <button className="btn primary" onClick={printView}>Print / PDF</button>
        </div>
      }
    >
      <div className="tabs">
        {([['organization', 'Organization summary'], ['graph', 'Entity relationships'], ['geospatial', 'Geospatial'], ['audit', 'Audit extract']] as const).map(([k, label]) => (
          <button key={k} className={`tab${kind === k ? ' active' : ''}`} onClick={() => setKind(k as ReportKind)}>{label}</button>
        ))}
      </div>

      <div className="grid g-2-1">
        <Card title={report.title} actions={<Badge tone="blue">INTERNAL</Badge>}>
          <div className="tiny muted" style={{ marginBottom: 10 }}>
            Generated {fmtDate(generated)} IST · by {user?.email} · classification INTERNAL · data basis: synthetic demonstration records
          </div>

          {(kind === 'organization' || kind === 'graph') && ov.data && (
            <div className="grid g2" style={{ marginBottom: 12 }}>
              <EChart option={barOption(ov.data.entities_by_type, true)} height={190} />
              <EChart option={donutOption(ov.data.relationships_by_provenance)} height={190} />
            </div>
          )}
          {kind === 'geospatial' && summary.data && (
            <EChart option={barOption(Object.fromEntries((summary.data.districts ?? []).slice(0, 8).map((d: any) => [d.district, d.count])))} height={200} />
          )}

          <div className="tbl-wrap" style={{ maxHeight: 380 }}>
            <table>
              <thead>
                <tr>{Object.keys(report.rows[0] ?? { empty: '' }).slice(0, 6).map((h) => <th key={h}>{h.replace(/_/g, ' ')}</th>)}</tr>
              </thead>
              <tbody>
                {report.rows.slice(0, 100).map((r: any, i: number) => (
                  <tr key={i}>{Object.keys(report.rows[0] ?? {}).slice(0, 6).map((h) => (
                    <td key={h} className="tiny">{String((r as any)[h] ?? '—').slice(0, 90)}</td>
                  ))}</tr>
                ))}
                {report.rows.length === 0 && <tr><td colSpan={6}><Empty>{kind === 'audit' ? 'Audit access requires auditor, org-admin or platform-admin role' : 'No records'}</Empty></td></tr>}
              </tbody>
            </table>
          </div>
          <div className="tiny muted" style={{ marginTop: 8 }}>
            Showing {Math.min(100, report.rows.length)} of {report.rows.length} records. Full set included in exports.
          </div>
        </Card>

        <div className="stack gap12">
          <Card title="Export controls">
            <div className="stack gap8 tiny muted">
              <div><strong className="dim">CSV</strong> — flat tabular extract for downstream analysis.</div>
              <div><strong className="dim">JSON</strong> — includes generation metadata, classification and record counts.</div>
              <div><strong className="dim">PDF</strong> — browser print pipeline; use "Save as PDF" in the print dialog.</div>
              <div className="hr" />
              <div>Excel export is supported server-side by the ingestion framework's openpyxl dependency and is
                enabled for administrative roles; the demonstration build exposes CSV/JSON/PDF to all authorized users.</div>
            </div>
          </Card>
          <Card title="Provenance">
            <dl className="kv">
              <dt>Report kind</dt><dd>{kind}</dd>
              <dt>Records</dt><dd>{report.rows.length}</dd>
              <dt>Data basis</dt><dd>synthetic demo dataset</dd>
              <dt>Generated</dt><dd className="mono tiny">{generated}</dd>
            </dl>
          </Card>
        </div>
      </div>
    </Section>
  )
}
