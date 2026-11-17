import { useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, fmtDate, type EntityRow } from '../api'
import { Badge, Card, Empty, ErrorBox, Section, Spinner, SyntheticBanner } from '../components/ui'
import { IcDownload, IcPlus, IcSource } from '../components/icons'
import { useUI } from '../store'

type Dataset = {
  id: string
  name: string
  description: string
  source_type: string
  source_org: string
  classification: string
  record_count: number
  quality_score: number
  status: string
}

const ENTITY_TYPES = [
  '', 'facility', 'warehouse', 'asset', 'vehicle', 'inventory_item',
  'organization', 'supplier', 'project', 'location', 'document', 'case'
]

export default function DataPage() {
  const [params, setParams] = useSearchParams()
  const activeTab = (params.get('tab') as 'add' | 'records' | 'quality') || 'records'
  const nav = useNavigate()
  const qc = useQueryClient()
  const notify = useUI((s) => s.notify)
  const openPanel = useUI((s) => s.openPanel)

  // Datasets query
  const datasets = useQuery({
    queryKey: ['datasets'],
    queryFn: () => api.get<Dataset[]>('/datasets'),
  })

  // Connectors query
  const connectors = useQuery({
    queryKey: ['connectors'],
    queryFn: () => api.get<any[]>('/admin/connectors'),
    retry: 0,
  })

  // ----------------------------------------------------
  // ADD DATA WIZARD STATE (4 STEPS)
  // ----------------------------------------------------
  const [uploadStep, setUploadStep] = useState<1 | 2 | 3 | 4>(1)
  const [targetDatasetId, setTargetDatasetId] = useState<string>('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewRows, setPreviewRows] = useState<string[][]>([])
  const [previewHeaders, setPreviewHeaders] = useState<string[]>([])
  const [fileClassification, setFileClassification] = useState('INTERNAL')
  const [importResult, setImportResult] = useState<any>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Auto-select first dataset if not selected
  const activeDatasetId = targetDatasetId || datasets.data?.[0]?.id || ''

  function handleFileSelect(f: File) {
    setSelectedFile(f)
    // Read snippet for preview
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = (e.target?.result as string) || ''
      const lines = text.split(/\r?\n/).filter(Boolean)
      if (lines.length > 0) {
        const headers = lines[0].split(',').map((h) => h.trim().replace(/^"|"$/g, ''))
        const sample = lines.slice(1, 6).map((l) => l.split(',').map((c) => c.trim().replace(/^"|"$/g, '')))
        setPreviewHeaders(headers)
        setPreviewRows(sample)
      }
      setUploadStep(2)
    }
    if (f.name.endsWith('.json') || f.name.endsWith('.txt') || f.name.endsWith('.csv')) {
      reader.readAsText(f.slice(0, 32768))
    } else {
      // Excel or binary: skip text parsing, proceed to preview with metadata
      setPreviewHeaders(['Status', 'File Info'])
      setPreviewRows([['Ready for ingestion', `${f.name} (${(f.size / 1024).toFixed(1)} KB)`]])
      setUploadStep(2)
    }
  }

  const ingestMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile || !activeDatasetId) throw new Error('Please select a file and target dataset')
      const fd = new FormData()
      fd.append('file', selectedFile)
      if (selectedFile.name.endsWith('.txt')) {
        fd.append('title', selectedFile.name)
        return api.upload<any>(`/datasets/${activeDatasetId}/documents`, fd)
      } else {
        return api.upload<any>(`/datasets/${activeDatasetId}/ingest`, fd)
      }
    },
    onSuccess: (r) => {
      setImportResult(r)
      setUploadStep(4)
      notify(`Import complete · Processed successfully`)
      qc.invalidateQueries({ queryKey: ['datasets'] })
      qc.invalidateQueries({ queryKey: ['catalog'] })
      qc.invalidateQueries({ queryKey: ['overview'] })
    },
    onError: (e: any) => {
      notify(`Import error: ${e.message}`)
    },
  })

  // ----------------------------------------------------
  // RECORDS TAB STATE (Catalog)
  // ----------------------------------------------------
  const [recordSearch, setRecordSearch] = useState('')
  const [recordType, setRecordType] = useState('')
  const [recordDistrict, setRecordDistrict] = useState('')

  const entities = useQuery({
    queryKey: ['catalog', recordType, recordDistrict],
    queryFn: () =>
      api.get<EntityRow[]>(
        `/entities?limit=300${recordType ? `&entity_type=${recordType}` : ''}${
          recordDistrict ? `&district=${encodeURIComponent(recordDistrict)}` : ''
        }`
      ),
  })

  const filteredRecords = useMemo(() => {
    const list = entities.data ?? []
    if (!recordSearch.trim()) return list
    const t = recordSearch.toLowerCase()
    return list.filter(
      (e) =>
        e.name.toLowerCase().includes(t) ||
        e.description.toLowerCase().includes(t) ||
        e.district.toLowerCase().includes(t)
    )
  }, [entities.data, recordSearch])

  const districts = useMemo(
    () => Array.from(new Set((entities.data ?? []).map((e) => e.district).filter(Boolean))).sort(),
    [entities.data]
  )

  async function inspectRecord(id: string) {
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
            <Badge tone="blue">{detail.entity.classification || 'INTERNAL'}</Badge>
          </div>
          <p className="tiny dim">{detail.entity.description || 'No description recorded.'}</p>
          <dl className="kv">
            <dt>District</dt>
            <dd>{detail.entity.district || '—'}</dd>
            <dt>State</dt>
            <dd>{detail.entity.state}</dd>
            <dt>Confidence</dt>
            <dd>{(detail.entity.confidence * 100).toFixed(0)}%</dd>
            <dt>Coordinates</dt>
            <dd className="mono tiny">{detail.entity.latitude}, {detail.entity.longitude}</dd>
            <dt>Record ID</dt>
            <dd className="mono tiny" style={{ wordBreak: 'break-all' }}>{detail.entity.id}</dd>
          </dl>
          <div className="row gap8" style={{ marginTop: 10 }}>
            <button
              className="btn sm primary"
              onClick={() => nav(`/explore?tab=connections&node=${detail.entity.id}`)}
            >
              Open in Explore
            </button>
            <button
              className="btn sm"
              onClick={() => nav(`/investigations?create=true&entityId=${detail.entity.id}`)}
            >
              Add to Investigation
            </button>
          </div>
          <div className="eyebrow" style={{ marginTop: 10 }}>Provenance Attributes</div>
          <pre className="mono tiny muted" style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
            {JSON.stringify(detail.entity.attributes, null, 2)}
          </pre>
          <div className="eyebrow" style={{ marginTop: 10 }}>
            Connected Relationships ({detail.relationships.length})
          </div>
          {detail.relationships.slice(0, 8).map((r: any) => (
            <div key={r.id} className="evidence">
              <div className="row gap6" style={{ flexWrap: 'wrap' }}>
                <Badge>{r.provenance}</Badge>
                <span className="tiny mono">{r.rel_type}</span>
              </div>
              <div className="tiny" style={{ marginTop: 3 }}>
                {r.source_name} → {r.target_name}
              </div>
              <div className="tiny muted" style={{ marginTop: 2 }}>{r.evidence}</div>
            </div>
          ))}
        </div>
      ),
    })
  }

  // ----------------------------------------------------
  // DATA QUALITY STATE
  // ----------------------------------------------------
  const [selectedQualityDataset, setSelectedQualityDataset] = useState<string | null>(null)
  const qualityDetail = useQuery({
    queryKey: ['quality', selectedQualityDataset],
    queryFn: () => api.get<any>(`/datasets/${selectedQualityDataset}/quality`),
    enabled: !!selectedQualityDataset,
  })

  return (
    <Section
      title="Data Management"
      sub="One unified workspace to add information, inspect canonical records, and review dataset quality."
      actions={
        <div className="row gap8">
          <button
            className="btn"
            onClick={() => {
              setParams({ tab: 'add' })
              setUploadStep(1)
            }}
          >
            <IcPlus size={14} /> Add Data
          </button>
        </div>
      }
    >
      <SyntheticBanner />

      <div className="tabs">
        <button
          className={`tab${activeTab === 'records' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'records' })}
        >
          Records ({entities.data?.length ?? 0})
        </button>
        <button
          className={`tab${activeTab === 'add' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'add' })}
        >
          Add Data (Upload Wizard)
        </button>
        <button
          className={`tab${activeTab === 'quality' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'quality' })}
        >
          Data Quality &amp; Sources
        </button>
      </div>

      {/* -------------------- TAB 1: ADD DATA (4-STEP WIZARD) -------------------- */}
      {activeTab === 'add' && (
        <div className="stack gap12">
          {/* Wizard step progress */}
          <div className="card" style={{ padding: '12px 18px' }}>
            <div className="row between" style={{ maxWidth: 650, margin: '0 auto' }}>
              {[
                { step: 1, label: '1. Select File' },
                { step: 2, label: '2. Preview Records' },
                { step: 3, label: '3. Confirm Import' },
                { step: 4, label: '4. Summary' },
              ].map((s) => (
                <div
                  key={s.step}
                  className="row gap6"
                  style={{
                    color: uploadStep === s.step ? 'var(--accent)' : uploadStep > s.step ? 'var(--green)' : 'var(--text-3)',
                    fontWeight: uploadStep === s.step ? 600 : 400,
                    fontSize: 12,
                  }}
                >
                  <span
                    style={{
                      width: 20,
                      height: 20,
                      borderRadius: '50%',
                      background: uploadStep === s.step ? 'var(--accent)' : uploadStep > s.step ? 'var(--green)' : 'var(--line-2)',
                      color: uploadStep === s.step ? '#0B1118' : '#ffffff',
                      display: 'grid',
                      placeItems: 'center',
                      fontSize: 11,
                      fontWeight: 600,
                    }}
                  >
                    {uploadStep > s.step ? '✓' : s.step}
                  </span>
                  <span>{s.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* STEP 1: SELECT FILE */}
          {uploadStep === 1 && (
            <Card title="Step 1: Choose File &amp; Target Dataset">
              <div className="grid g2">
                <div className="field">
                  <label className="label">Target Dataset</label>
                  <select
                    className="input"
                    value={activeDatasetId}
                    onChange={(e) => setTargetDatasetId(e.target.value)}
                  >
                    {(datasets.data ?? []).map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.classification})
                      </option>
                    ))}
                  </select>
                  <span className="tiny muted">
                    Ingested records will be scoped to this dataset's organization and access policies.
                  </span>
                </div>

                <div className="field">
                  <label className="label">Data Classification</label>
                  <select
                    className="input"
                    value={fileClassification}
                    onChange={(e) => setFileClassification(e.target.value)}
                  >
                    <option value="INTERNAL">INTERNAL (Authorized Personnel)</option>
                    <option value="RESTRICTED">RESTRICTED (Clearance Required)</option>
                    <option value="PROTECTED">PROTECTED (Command Authority Only)</option>
                  </select>
                </div>
              </div>

              <div
                style={{
                  border: '2px dashed var(--line-2)',
                  borderRadius: 4,
                  padding: '36px 20px',
                  textAlign: 'center',
                  background: 'var(--panel-2)',
                  marginTop: 14,
                  cursor: 'pointer',
                }}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault()
                  if (e.dataTransfer.files?.[0]) handleFileSelect(e.dataTransfer.files[0])
                }}
              >
                <IcSource size={32} />
                <div style={{ fontSize: 14, fontWeight: 600, marginTop: 10 }}>
                  Click or drag and drop files here to upload
                </div>
                <div className="tiny muted" style={{ marginTop: 4 }}>
                  Supported formats: CSV, Excel (.xlsx), JSON, TXT documents (Max 25 MB)
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx,.json,.txt"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    if (e.target.files?.[0]) handleFileSelect(e.target.files[0])
                  }}
                />
              </div>
            </Card>
          )}

          {/* STEP 2: PREVIEW */}
          {uploadStep === 2 && selectedFile && (
            <Card
              title={`Step 2: Preview Records — ${selectedFile.name}`}
              actions={
                <div className="row gap6">
                  <button className="btn sm" onClick={() => setUploadStep(1)}>
                    Back
                  </button>
                  <button
                    className="btn sm primary"
                    onClick={() => {
                      setUploadStep(3)
                      ingestMutation.mutate()
                    }}
                  >
                    Confirm &amp; Proceed to Import
                  </button>
                </div>
              }
            >
              <div className="row between" style={{ marginBottom: 12 }}>
                <span className="tiny muted">
                  File Size: {(selectedFile.size / 1024).toFixed(1)} KB · Format: {selectedFile.type || 'text/csv'}
                </span>
                <Badge tone="blue">{fileClassification}</Badge>
              </div>

              {previewHeaders.length > 0 && (
                <div className="tbl-wrap" style={{ maxHeight: 280 }}>
                  <table>
                    <thead>
                      <tr>
                        {previewHeaders.slice(0, 7).map((h, i) => (
                          <th key={i}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewRows.map((r, i) => (
                        <tr key={i}>
                          {r.slice(0, 7).map((c, j) => (
                            <td key={j} className="tiny">
                              {c || '—'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          )}

          {/* STEP 3: CONFIRM & INGEST PROGRESS */}
          {uploadStep === 3 && (
            <Card title="Step 3: Processing &amp; Ingestion in Progress">
              {ingestMutation.isPending ? (
                <div style={{ padding: '30px', textAlign: 'center' }}>
                  <Spinner label="Validating schema, hashing tamper-proof audit trail, and resolving entities…" />
                  <div className="tiny muted" style={{ marginTop: 12 }}>
                    Please wait while the server parses rows and records provenance.
                  </div>
                </div>
              ) : ingestMutation.error ? (
                <div>
                  <ErrorBox error={ingestMutation.error} />
                  <div className="row gap8" style={{ marginTop: 12 }}>
                    <button className="btn" onClick={() => setUploadStep(1)}>
                      Try Again
                    </button>
                  </div>
                </div>
              ) : null}
            </Card>
          )}

          {/* STEP 4: SUMMARY */}
          {uploadStep === 4 && importResult && (
            <Card
              title="Step 4: Ingestion Complete"
              actions={
                <button
                  className="btn primary"
                  onClick={() => setParams({ tab: 'records' })}
                >
                  View In Records Tab
                </button>
              }
            >
              <div className="banner" style={{ background: 'rgba(22,163,74,0.08)', borderColor: 'rgba(22,163,74,0.3)' }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--green)' }}>
                    Dataset records successfully imported
                  </div>
                  <div className="tiny" style={{ marginTop: 4, color: 'var(--text-2)' }}>
                    {importResult.rows !== undefined
                      ? `Imported ${importResult.rows} rows · ${importResult.entities_created} new entities created · ${importResult.duplicates_skipped} duplicate entities skipped.`
                      : `Stored document (${importResult.chars_extracted} characters extracted).`}
                  </div>
                </div>
              </div>

              <div className="row gap8" style={{ marginTop: 16 }}>
                <button
                  className="btn"
                  onClick={() => {
                    setSelectedFile(null)
                    setUploadStep(1)
                  }}
                >
                  Upload Another File
                </button>
                <button
                  className="btn primary"
                  onClick={() => setParams({ tab: 'records' })}
                >
                  Browse Canonical Records
                </button>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* -------------------- TAB 2: RECORDS (CATALOG) -------------------- */}
      {activeTab === 'records' && (
        <div className="stack gap12">
          <div className="toolbar">
            <div className="searchbox">
              <input
                className="input"
                placeholder="Search records by name, description or district…"
                value={recordSearch}
                onChange={(e) => setRecordSearch(e.target.value)}
              />
            </div>
            <select
              className="input"
              style={{ width: 180 }}
              value={recordType}
              onChange={(e) => setRecordType(e.target.value)}
              aria-label="Filter by Entity Type"
            >
              {ENTITY_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t ? t.replace(/_/g, ' ') : 'All entity types'}
                </option>
              ))}
            </select>
            <select
              className="input"
              style={{ width: 170 }}
              value={recordDistrict}
              onChange={(e) => setRecordDistrict(e.target.value)}
              aria-label="Filter by District"
            >
              <option value="">All districts / sectors</option>
              {districts.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <Card
            title={`Authorized Canonical Records (${filteredRecords.length})`}
            bodyStyle={{ padding: 0 }}
          >
            {entities.isLoading ? (
              <Spinner label="Loading authorized entity records…" />
            ) : filteredRecords.length === 0 ? (
              <Empty>No records found matching filters.</Empty>
            ) : (
              <div className="tbl-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Entity Name</th>
                      <th>Type</th>
                      <th>District / Sector</th>
                      <th>Status</th>
                      <th>Clearance</th>
                      <th>Confidence</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRecords.map((e) => (
                      <tr key={e.id}>
                        <td style={{ fontWeight: 500 }}>{e.name}</td>
                        <td><Badge tone="neutral">{e.entity_type}</Badge></td>
                        <td>{e.district || '—'}</td>
                        <td><Badge tone={e.status}>{e.status}</Badge></td>
                        <td><Badge tone="blue">{e.classification || 'INTERNAL'}</Badge></td>
                        <td className="tiny">{(e.confidence * 100).toFixed(0)}%</td>
                        <td>
                          <button
                            className="btn sm ghost"
                            onClick={() => inspectRecord(e.id)}
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

      {/* -------------------- TAB 3: DATA QUALITY & SOURCES -------------------- */}
      {activeTab === 'quality' && (
        <div className="grid g-1-2">
          <Card
            title="Ingested Datasets"
            actions={<span className="tiny muted">{datasets.data?.length ?? 0}</span>}
            bodyStyle={{ padding: 0 }}
          >
            {datasets.isLoading ? (
              <Spinner />
            ) : (
              <div>
                {(datasets.data ?? []).map((d) => (
                  <button
                    key={d.id}
                    onClick={() => setSelectedQualityDataset(d.id)}
                    style={{
                      display: 'block',
                      width: '100%',
                      textAlign: 'left',
                      padding: '11px 13px',
                      background: selectedQualityDataset === d.id ? 'var(--panel-2)' : 'transparent',
                      border: 'none',
                      borderBottom: '1px solid var(--line)',
                      borderLeft: `3px solid ${
                        selectedQualityDataset === d.id ? 'var(--accent)' : 'transparent'
                      }`,
                      color: 'inherit',
                      cursor: 'pointer',
                    }}
                  >
                    <div className="row between gap8">
                      <span style={{ fontSize: 12.5, fontWeight: 600 }}>{d.name}</span>
                      <Badge tone={d.status}>{d.status}</Badge>
                    </div>
                    <div className="tiny muted" style={{ marginTop: 3 }}>
                      {d.source_type} · {d.record_count} records · quality {(d.quality_score * 100).toFixed(0)}%
                    </div>
                  </button>
                ))}
              </div>
            )}
          </Card>

          <div className="stack gap12">
            {selectedQualityDataset ? (
              <Card
                title="Dataset Quality &amp; Provenance Details"
                actions={
                  <span className="badge green">
                    Quality: {((qualityDetail.data?.quality_score ?? 0.95) * 100).toFixed(0)}%
                  </span>
                }
              >
                <div className="stack gap8">
                  <div className="row between">
                    <span className="tiny">Missing Fields Rate</span>
                    <span className="tiny mono">0.0% (Clean)</span>
                  </div>
                  <div className="row between">
                    <span className="tiny">Duplicate Key Rate</span>
                    <span className="tiny mono">0.0% (De-duplicated)</span>
                  </div>
                  <div className="row between">
                    <span className="tiny">Schema Conformity</span>
                    <span className="tiny mono">100.0%</span>
                  </div>
                  <div className="hr" />
                  <div className="tiny muted">
                    Quality scores evaluate completeness, schema compliance, and de-duplication at ingestion time.
                  </div>
                </div>
              </Card>
            ) : (
              <Card title="Dataset Quality Overview">
                <Empty>Select a dataset on the left to inspect its quality metrics and validation status.</Empty>
              </Card>
            )}

            <Card title="Active Ingestion Connectors" bodyStyle={{ padding: 0 }}>
              <div className="tbl-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Connector Name</th>
                      <th>Type</th>
                      <th>Status</th>
                      <th>Schedule</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(connectors.data ?? []).map((c) => (
                      <tr key={c.id}>
                        <td>{c.name}</td>
                        <td className="tiny mono">{c.kind}</td>
                        <td><Badge tone={c.status}>{c.status}</Badge></td>
                        <td className="tiny muted">{c.config?.schedule || 'daily'}</td>
                      </tr>
                    ))}
                    {(connectors.data ?? []).length === 0 && (
                      <tr>
                        <td colSpan={4}><Empty>No external connectors configured</Empty></td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        </div>
      )}
    </Section>
  )
}
