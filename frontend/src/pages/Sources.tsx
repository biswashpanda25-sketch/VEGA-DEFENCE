import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, fmtDate } from '../api'
import { Badge, Card, Empty, ErrorBox, Section, Spinner } from '../components/ui'
import { useUI } from '../store'

type Dataset = {
  id: string; name: string; description: string; source_type: string; source_org: string
  classification: string; record_count: number; quality_score: number; status: string
}

export default function Sources() {
  const qc = useQueryClient()
  const notify = useUI((s) => s.notify)
  const [selected, setSelected] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [docFile, setDocFile] = useState<File | null>(null)
  const [result, setResult] = useState<any>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const datasets = useQuery({ queryKey: ['datasets'], queryFn: () => api.get<Dataset[]>('/datasets') })
  const connectors = useQuery({
    queryKey: ['connectors'],
    queryFn: () => api.get<any[]>('/admin/connectors'),
    retry: 0,
  })
  const quality = useQuery({
    queryKey: ['quality', selected],
    queryFn: () => api.get<any>(`/datasets/${selected}/quality`),
    enabled: !!selected,
  })

  const ingest = useMutation({
    mutationFn: async ({ id, f }: { id: string; f: File }) => {
      const fd = new FormData()
      fd.append('file', f)
      return api.upload<any>(`/datasets/${id}/ingest`, fd)
    },
    onSuccess: (r) => {
      setResult(r)
      notify(`Ingested ${r.rows} rows · ${r.entities_created} new · ${r.duplicates_skipped} duplicates skipped`)
      qc.invalidateQueries({ queryKey: ['datasets'] })
      qc.invalidateQueries({ queryKey: ['overview'] })
    },
  })

  const uploadDoc = useMutation({
    mutationFn: async ({ id, f }: { id: string; f: File }) => {
      const fd = new FormData()
      fd.append('file', f)
      fd.append('title', f.name)
      return api.upload<any>(`/datasets/${id}/documents`, fd)
    },
    onSuccess: (r) => notify(`Document stored · ${r.chars_extracted} characters extracted`),
  })

  const active = (datasets.data ?? []).find((d) => d.id === selected)

  return (
    <Section title="Data Sources" sub="Authorized connectors, ingestion pipelines and dataset quality. Connectors never bypass authentication or rate limits.">
      {datasets.error && <ErrorBox error={datasets.error} />}
      <div className="grid g-1-2">
        <Card title="Datasets" actions={<span className="tiny muted">{datasets.data?.length ?? 0}</span>} bodyStyle={{ padding: 0 }}>
          {datasets.isLoading ? <Spinner /> : (
            <div>
              {(datasets.data ?? []).map((d) => (
                <button key={d.id} onClick={() => { setSelected(d.id); setResult(null) }}
                  style={{
                    display: 'block', width: '100%', textAlign: 'left', padding: '10px 12px',
                    background: selected === d.id ? 'var(--panel-2)' : 'transparent',
                    border: 'none', borderBottom: '1px solid var(--line)',
                    borderLeft: `2px solid ${selected === d.id ? 'var(--accent)' : 'transparent'}`,
                    color: 'inherit',
                  }}>
                  <div className="row between gap8">
                    <span style={{ fontSize: 12.5 }}>{d.name}</span>
                    <Badge>{d.status}</Badge>
                  </div>
                  <div className="tiny muted" style={{ marginTop: 2 }}>
                    {d.source_type} · {d.record_count} records · quality {(d.quality_score * 100).toFixed(0)}%
                  </div>
                </button>
              ))}
              {datasets.data?.length === 0 && <Empty>No datasets in this organization</Empty>}
            </div>
          )}
        </Card>

        <div className="stack gap12">
          {!active && (
            <Card title="Ingestion pipeline">
              <Empty>Select a dataset to inspect its pipeline, quality metrics and ingestion controls.</Empty>
            </Card>
          )}
          {active && (
            <>
              <Card title={active.name} actions={<Badge tone="blue">{active.classification}</Badge>}>
                <p className="tiny dim" style={{ marginTop: 0 }}>{active.description}</p>
                <div className="kv" style={{ marginTop: 10 }}>
                  <dt>Dataset ID</dt><dd className="mono tiny">{active.id}</dd>
                  <dt>Source type</dt><dd>{active.source_type}</dd>
                  <dt>Source org</dt><dd>{active.source_org || '—'}</dd>
                  <dt>Records</dt><dd>{active.record_count}</dd>
                  <dt>Quality score</dt><dd>{(active.quality_score * 100).toFixed(1)}%</dd>
                </div>

                <div className="hr" />
                <div className="eyebrow" style={{ marginBottom: 8 }}>Ingest file</div>
                <div className="row gap8" style={{ flexWrap: 'wrap' }}>
                  <input ref={fileRef} type="file" accept=".csv,.json,.xlsx" style={{ display: 'none' }}
                    onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
                  <button className="btn" onClick={() => fileRef.current?.click()}>Choose CSV / JSON / XLSX</button>
                  <span className="tiny muted">{file?.name ?? 'no file selected'}</span>
                  <button className="btn primary" disabled={!file || ingest.isPending}
                    onClick={() => file && ingest.mutate({ id: active.id, f: file })}>
                    {ingest.isPending ? <><span className="spinner" /> Ingesting…</> : 'Run ingestion'}
                  </button>
                </div>
                {ingest.error && <div style={{ marginTop: 10 }}><ErrorBox error={ingest.error} /></div>}
                {result && (
                  <div className="banner" style={{ marginTop: 10 }}>
                    <div className="stack gap4" style={{ width: '100%' }}>
                      <div className="row gap12">
                        <span>Rows parsed: <strong>{result.rows}</strong></span>
                        <span>Created: <strong>{result.entities_created}</strong></span>
                        <span>Duplicates skipped: <strong>{result.duplicates_skipped}</strong></span>
                      </div>
                      <div className="tiny muted">Provenance retained: {JSON.stringify(result.provenance)}</div>
                    </div>
                  </div>
                )}

                <div className="hr" />
                <div className="eyebrow" style={{ marginBottom: 8 }}>Attach document</div>
                <div className="row gap8" style={{ flexWrap: 'wrap' }}>
                  <input type="file" accept=".pdf,.txt,.md" onChange={(e) => setDocFile(e.target.files?.[0] ?? null)} />
                  <button className="btn" disabled={!docFile || uploadDoc.isPending}
                    onClick={() => docFile && uploadDoc.mutate({ id: active.id, f: docFile })}>
                    Upload
                  </button>
                </div>
                <div className="tiny muted" style={{ marginTop: 6 }}>
                  PDFs are stored with raw-text extraction only in this build; OCR is not enabled.
                </div>
              </Card>

              <Card title="Data quality" actions={<span className="tiny muted">computed live</span>}>
                {quality.isLoading ? <Spinner /> : quality.data && (
                  <div className="grid g4">
                    {[
                      ['Completeness', quality.data.completeness],
                      ['Uniqueness', quality.data.uniqueness],
                      ['Validity', quality.data.validity],
                      ['Provenance', quality.data.provenance_coverage],
                    ].map(([label, v]: any) => (
                      <div key={label}>
                        <div className="tiny muted">{label}</div>
                        <div style={{ fontSize: 18, marginTop: 3 }}>{(v * 100).toFixed(0)}%</div>
                        <div style={{ height: 3, background: 'var(--line)', marginTop: 5, borderRadius: 2 }}>
                          <div style={{ height: 3, width: `${v * 100}%`, background: v > 0.8 ? 'var(--green)' : v > 0.5 ? 'var(--amber)' : 'var(--red)', borderRadius: 2 }} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <div className="tiny muted" style={{ marginTop: 10 }}>
                  Organization score is the weighted composite of completeness (40%), uniqueness (30%), validity (20%) and provenance coverage (10%).
                </div>
              </Card>
            </>
          )}

          <Card title="Connectors" actions={<span className="tiny muted">{connectors.data?.length ?? 0} configured</span>}>
            {connectors.error ? (
              <Empty>Connector administration requires data-admin, org-admin or platform-admin role.</Empty>
            ) : connectors.isLoading ? <Spinner /> : (
              <div className="tbl-wrap">
                <table>
                  <thead><tr><th>Name</th><th>Kind</th><th>Status</th><th>Last error</th></tr></thead>
                  <tbody>
                    {(connectors.data ?? []).map((c) => (
                      <tr key={c.id}>
                        <td>{c.name}</td>
                        <td><Badge tone="neutral">{c.kind}</Badge></td>
                        <td><Badge>{c.status}</Badge></td>
                        <td className="tiny muted">{c.last_error ?? '—'}</td>
                      </tr>
                    ))}
                    {(connectors.data ?? []).length === 0 && <tr><td colSpan={4}><Empty>No connectors configured</Empty></td></tr>}
                  </tbody>
                </table>
              </div>
            )}
            <div className="tiny muted" style={{ marginTop: 8 }}>
              REST and database connectors are implemented as adapters but require authorized institutional endpoints and credentials.
              No external integration is claimed operational in this build.
            </div>
          </Card>
        </div>
      </div>
    </Section>
  )
}
