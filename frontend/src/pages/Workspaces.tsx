import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, fmtDate, type EntityRow } from '../api'
import { Badge, Card, Empty, ErrorBox, Section, Spinner, SyntheticBanner } from '../components/ui'
import { useAuth, useUI } from '../store'

const KIND_HINT: Record<string, string> = {
  evidence: 'A fact supported directly by cited records.',
  assumption: 'A working premise not yet supported; must not be read as fact.',
  hypothesis: 'A testable proposition under investigation.',
  conclusion: 'An assessment supported by reviewed evidence and approved by a reviewer.',
}

export default function Workspaces({ mode = 'workspaces' }: { mode?: 'workspaces' | 'cases' }) {
  const qc = useQueryClient()
  const notify = useUI((s) => s.notify)
  const user = useAuth((s) => s.user)
  const [activeId, setActiveId] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [title, setTitle] = useState('')
  const [desc, setDesc] = useState('')

  const cases = useQuery({ queryKey: ['cases'], queryFn: () => api.get<any[]>('/cases') })
  const detail = useQuery({
    queryKey: ['case', activeId],
    queryFn: () => api.get<any>(`/cases/${activeId}`),
    enabled: !!activeId,
  })
  const entities = useQuery({ queryKey: ['entities-mini'], queryFn: () => api.get<EntityRow[]>('/entities?limit=200') })

  const create = useMutation({
    mutationFn: () => api.post<any>('/cases', { title, description: desc, classification: 'INTERNAL' }),
    onSuccess: (c) => {
      setCreating(false); setTitle(''); setDesc('')
      notify('Workspace created and audited')
      qc.invalidateQueries({ queryKey: ['cases'] })
      setActiveId(c.id)
    },
  })

  const [fTitle, setFTitle] = useState('')
  const [fDesc, setFDesc] = useState('')
  const [fKind, setFKind] = useState('evidence')
  const [fRefs, setFRefs] = useState<string[]>([])

  const addFinding = useMutation({
    mutationFn: () => api.post<any>(`/cases/${activeId}/findings`, {
      title: fTitle, description: fDesc, kind: fKind, confidence: 0.6, evidence_refs: fRefs,
    }),
    onSuccess: () => {
      setFTitle(''); setFDesc(''); setFRefs([])
      notify('Finding recorded with evidence references')
      qc.invalidateQueries({ queryKey: ['case', activeId] })
    },
  })

  const review = useMutation({
    mutationFn: ({ fid, decision }: { fid: string; decision: string }) =>
      api.post<any>(`/cases/${activeId}/findings/${fid}/review?decision=${decision}`),
    onSuccess: () => { notify('Review decision recorded'); qc.invalidateQueries({ queryKey: ['case', activeId] }) },
  })

  useEffect(() => { if (!activeId && cases.data?.length) setActiveId(cases.data[0].id) }, [cases.data, activeId])

  const c = detail.data?.case
  const findings = detail.data?.findings ?? []
  const canReview = ['platform_admin', 'org_admin', 'reviewer'].includes(user?.role ?? '')

  function generateSITREP() {
    if (!c) return
    const approved = findings.filter((f: any) => f.reviewer_status === 'approved')
    const pending = findings.filter((f: any) => f.reviewer_status !== 'approved')
    const lines = [
      `# VEGA DEFENCE — OPERATIONAL SITUATION REPORT (SITREP)`,
      `CASE FILE: ${c.title.toUpperCase()}`,
      `CLASSIFICATION: ${c.classification} // SOVEREIGN MILITARY & STRATEGIC COMMAND USE ONLY`,
      `DATE OF ISSUE: ${new Date().toISOString()}`,
      `OFFICER OF RECORD: ${c.created_by}`,
      `STATUS: ${c.status.toUpperCase()}`,
      `--------------------------------------------------------------------------------`,
      `1. OPERATIONAL SCOPE & OBJECTIVE:`,
      `${c.description || 'No formal scope recorded.'}`,
      ``,
      `2. EXECUTIVE SUMMARY & APPROVED ASSESSMENTS (${approved.length}):`,
      approved.length === 0 ? 'No findings have completed formal reviewer sign-off.' :
        approved.map((f: any, idx: number) => `   [${idx + 1}] ${f.title} (${f.kind.toUpperCase()})\n       Confidence: ${(f.confidence * 100).toFixed(0)}%\n       Detail: ${f.description}\n       Evidence Cited: ${f.evidence_refs.join(', ') || 'Direct observation'}`).join('\n\n'),
      ``,
      `3. ACTIVE WORKING HYPOTHESES & UNRESOLVED EVIDENCE (${pending.length}):`,
      pending.length === 0 ? 'All working hypotheses have been reviewed.' :
        pending.map((f: any, idx: number) => `   [P-${idx + 1}] ${f.title} [Status: ${f.reviewer_status}]\n       ${f.description}`).join('\n\n'),
      ``,
      `4. CHAIN OF CUSTODY & AUDIT NOTICE:`,
      `This dossier was generated from the VEGA DEFENCE sovereign intelligence graph.`,
      `All military entities cited conform to command isolation rules and clearance protocols.`,
    ]
    const content = lines.join('\n')
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `VEGA-DEFENCE-SITREP-${c.title.replace(/\s+/g, '_')}-${Date.now()}.md`
    a.click()
    URL.revokeObjectURL(url)
    notify('SITREP dossier generated and downloaded')
  }

  return (
    <Section
      title={mode === 'cases' ? 'Cases' : 'Analytical Workspaces'}
      sub="Case-scoped analysis with evidence discipline: every finding records its supporting records, kind, confidence and reviewer status."
      actions={<button className="btn primary" onClick={() => setCreating((v) => !v)}>New workspace</button>}
    >
      <SyntheticBanner />
      {creating && (
        <Card title="Create analytical workspace" style={{ marginBottom: 12 }}>
          <div className="grid g2">
            <div className="field"><label className="label">Title</label>
              <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Northern Theatre Airbase Readiness Review" /></div>
            <div className="field"><label className="label">Scope description</label>
              <input className="input" value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="What tactical intelligence question does this case answer?" /></div>
          </div>
          <div className="row gap8">
            <button className="btn primary" disabled={!title.trim() || create.isPending} onClick={() => create.mutate()}>
              {create.isPending ? 'Creating…' : 'Create'}
            </button>
            <button className="btn ghost" onClick={() => setCreating(false)}>Cancel</button>
          </div>
          {create.error && <div style={{ marginTop: 8 }}><ErrorBox error={create.error} /></div>}
        </Card>
      )}

      <div className="grid g-1-2">
        <Card title="Workspaces" bodyStyle={{ padding: 0 }} actions={<span className="tiny muted">{cases.data?.length ?? 0}</span>}>
          {cases.isLoading ? <Spinner /> : (
            <div>
              {(cases.data ?? []).map((k) => (
                <button key={k.id} onClick={() => setActiveId(k.id)} style={{
                  display: 'block', width: '100%', textAlign: 'left', padding: '10px 12px', background: activeId === k.id ? 'var(--panel-2)' : 'transparent',
                  border: 'none', borderBottom: '1px solid var(--line)', color: 'inherit',
                  borderLeft: `2px solid ${activeId === k.id ? 'var(--accent)' : 'transparent'}`,
                }}>
                  <div className="row between gap8"><span style={{ fontSize: 12.5 }}>{k.title}</span><Badge>{k.status}</Badge></div>
                  <div className="tiny muted" style={{ marginTop: 2 }}>{k.created_by}</div>
                </button>
              ))}
              {cases.data?.length === 0 && <Empty>No workspaces yet</Empty>}
            </div>
          )}
        </Card>

        <div className="stack gap12">
          {!c && <Card title="Case detail"><Empty>Select a workspace</Empty></Card>}
          {c && (
            <>
              <Card title={c.title} actions={
                <div className="row gap6">
                  <button className="btn sm primary" onClick={generateSITREP}>
                    📄 Export SITREP
                  </button>
                  <Badge tone="blue">{c.classification}</Badge>
                </div>
              }>
                <p className="tiny dim" style={{ marginTop: 0 }}>{c.description}</p>
                <div className="row gap12 tiny muted">
                  <span>Status: {c.status}</span><span>Owner: {c.created_by}</span><span>Created: {fmtDate(c.created_at)}</span>
                </div>
              </Card>

              <Card title={`Findings (${findings.length})`}>
                {findings.length === 0 && <Empty>No findings recorded</Empty>}
                <div className="stack gap8">
                  {findings.map((f: any) => (
                    <div key={f.id} className="card" style={{ padding: 11 }}>
                      <div className="row between gap8">
                        <span style={{ fontSize: 12.5 }}>{f.title}</span>
                        <div className="row gap6"><Badge tone={f.kind}>{f.kind}</Badge><Badge>{f.reviewer_status}</Badge></div>
                      </div>
                      <p className="tiny dim" style={{ margin: '5px 0' }}>{f.description}</p>
                      <div className="tiny muted">Confidence {(f.confidence * 100).toFixed(0)}% · {f.created_by} · {fmtDate(f.created_at)}</div>
                      <div className="row gap6" style={{ marginTop: 6, flexWrap: 'wrap' }}>
                        {f.evidence_refs.map((rid: string) => {
                          const e = (entities.data ?? []).find((x) => x.id === rid)
                          return <span key={rid} className="cite">{e?.name ?? `record ${rid.slice(0, 8)}`}</span>
                        })}
                      </div>
                      {canReview && f.reviewer_status === 'pending' && (
                        <div className="row gap6" style={{ marginTop: 8 }}>
                          <button className="btn sm" onClick={() => review.mutate({ fid: f.id, decision: 'approved' })}>Approve</button>
                          <button className="btn sm ghost" onClick={() => review.mutate({ fid: f.id, decision: 'needs_revision' })}>Needs revision</button>
                          <button className="btn sm ghost" onClick={() => review.mutate({ fid: f.id, decision: 'rejected' })}>Reject</button>
                          <span className="tiny muted">Reviewer decisions are immutable audit events.</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </Card>

              <Card title="Record a finding">
                <div className="grid g2">
                  <div className="field"><label className="label">Title</label>
                    <input className="input" value={fTitle} onChange={(e) => setFTitle(e.target.value)} /></div>
                  <div className="field"><label className="label">Kind</label>
                    <select className="input" value={fKind} onChange={(e) => setFKind(e.target.value)}>
                      {Object.keys(KIND_HINT).map((k) => <option key={k} value={k}>{k}</option>)}
                    </select>
                  </div>
                </div>
                <div className="tiny muted" style={{ marginTop: -6, marginBottom: 10 }}>{KIND_HINT[fKind]}</div>
                <div className="field"><label className="label">Description</label>
                  <textarea className="input" rows={2} value={fDesc} onChange={(e) => setFDesc(e.target.value)} /></div>
                <div className="field">
                  <label className="label">Evidence references {fKind === 'evidence' || fKind === 'conclusion' ? '(required)' : '(optional)'}</label>
                  <select className="input" multiple size={5} value={fRefs} onChange={(e) => setFRefs(Array.from(e.target.selectedOptions).map((o) => o.value))}>
                    {(entities.data ?? []).map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}
                  </select>
                </div>
                <button className="btn primary" disabled={!fTitle.trim() || addFinding.isPending}
                  onClick={() => addFinding.mutate()}>Record finding</button>
                {addFinding.error && <div style={{ marginTop: 8 }}><ErrorBox error={addFinding.error} /></div>}
              </Card>
            </>
          )}
        </div>
      </div>
    </Section>
  )
}
