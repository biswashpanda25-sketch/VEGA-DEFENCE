import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, fmtDate, type EntityRow } from '../api'
import { Badge, Card, Empty, ErrorBox, Section, Spinner, SyntheticBanner } from '../components/ui'
import { useAuth, useUI } from '../store'
import { IcPlus, IcReport, IcCase, IcDownload } from '../components/icons'
import Reports from './Reports'

const KIND_HINT: Record<string, { label: string; desc: string; tone: string }> = {
  evidence: {
    label: 'Verified Evidence',
    desc: 'An empirical fact corroborated directly by authorized records or reconnaissance.',
    tone: 'teal',
  },
  hypothesis: {
    label: 'Working Hypothesis',
    desc: 'A testable proposition under active investigation.',
    tone: 'amber',
  },
  assumption: {
    label: 'Operational Assumption',
    desc: 'A working premise not yet supported by hard records; must not be treated as confirmed fact.',
    tone: 'blue',
  },
  conclusion: {
    label: 'Reviewed Assessment',
    desc: 'A synthesized evaluation supported by reviewed evidence and confirmed by an authorized reviewer.',
    tone: 'green',
  },
}

export default function InvestigationsPage() {
  const [params, setParams] = useSearchParams()
  const activeTab = (params.get('tab') as 'dossier' | 'findings' | 'review' | 'reports') || 'dossier'
  const caseIdFromUrl = params.get('caseId')
  const createFromUrl = params.get('create') === 'true'
  const nav = useNavigate()
  const qc = useQueryClient()
  const notify = useUI((s) => s.notify)
  const user = useAuth((s) => s.user)

  const [activeId, setActiveId] = useState<string | null>(caseIdFromUrl)
  const [creating, setCreating] = useState(createFromUrl)
  const [title, setTitle] = useState('')
  const [desc, setDesc] = useState('')
  const [classification, setClassification] = useState('INTERNAL')

  // Queries
  const cases = useQuery({ queryKey: ['cases'], queryFn: () => api.get<any[]>('/cases') })
  const detail = useQuery({
    queryKey: ['case', activeId],
    queryFn: () => api.get<any>(`/cases/${activeId}`),
    enabled: !!activeId,
  })
  const entities = useQuery({ queryKey: ['entities-mini'], queryFn: () => api.get<EntityRow[]>('/entities?limit=200') })

  // Auto-select first case if none active
  useEffect(() => {
    if (!activeId && cases.data?.length) {
      setActiveId(cases.data[0].id)
    }
  }, [cases.data, activeId])

  // Sync url param
  useEffect(() => {
    if (caseIdFromUrl && caseIdFromUrl !== activeId) {
      setActiveId(caseIdFromUrl)
    }
    if (createFromUrl) {
      setCreating(true)
    }
  }, [caseIdFromUrl, createFromUrl])

  // Create investigation mutation
  const createMutation = useMutation({
    mutationFn: () => api.post<any>('/cases', { title, description: desc, classification }),
    onSuccess: (c) => {
      setCreating(false)
      setTitle('')
      setDesc('')
      notify('Investigation created and audited in sovereign ledger')
      qc.invalidateQueries({ queryKey: ['cases'] })
      setActiveId(c.id)
      setParams({ caseId: c.id, tab: 'dossier' })
    },
  })

  // Finding form state
  const [fTitle, setFTitle] = useState('')
  const [fDesc, setFDesc] = useState('')
  const [fKind, setFKind] = useState('evidence')
  const [fConfidence, setFConfidence] = useState(0.8)
  const [fRefs, setFRefs] = useState<string[]>([])

  const addFinding = useMutation({
    mutationFn: () =>
      api.post<any>(`/cases/${activeId}/findings`, {
        title: fTitle,
        description: fDesc,
        kind: fKind,
        confidence: fConfidence,
        evidence_refs: fRefs,
      }),
    onSuccess: () => {
      setFTitle('')
      setFDesc('')
      setFRefs([])
      notify('Finding recorded with evidence citations')
      qc.invalidateQueries({ queryKey: ['case', activeId] })
    },
  })

  // Review decision mutation
  const reviewMutation = useMutation({
    mutationFn: ({ fid, decision }: { fid: string; decision: string }) =>
      api.post<any>(`/cases/${activeId}/findings/${fid}/review?decision=${decision}`),
    onSuccess: () => {
      notify('Review decision recorded and committed to audit log')
      qc.invalidateQueries({ queryKey: ['case', activeId] })
    },
  })

  const currentCase = detail.data?.case
  const findings = detail.data?.findings ?? []
  const canReview = ['platform_admin', 'org_admin', 'reviewer'].includes(user?.role ?? '')

  function generateSITREP() {
    if (!currentCase) return
    const approved = findings.filter((f: any) => f.reviewer_status === 'approved')
    const pending = findings.filter((f: any) => f.reviewer_status !== 'approved')
    const lines = [
      `# VEGA DEFENCE — OPERATIONAL SITUATION REPORT (SITREP)`,
      `CASE DOSSIER: ${currentCase.title.toUpperCase()}`,
      `CLASSIFICATION: ${currentCase.classification} // SOVEREIGN MILITARY & STRATEGIC COMMAND USE ONLY`,
      `DATE OF ISSUE: ${new Date().toISOString()}`,
      `OFFICER OF RECORD: ${currentCase.created_by}`,
      `STATUS: ${currentCase.status.toUpperCase()}`,
      `--------------------------------------------------------------------------------`,
      `1. OPERATIONAL SCOPE & OBJECTIVE:`,
      `${currentCase.description || 'No formal objective recorded.'}`,
      ``,
      `2. EXECUTIVE SUMMARY & APPROVED FINDINGS (${approved.length}):`,
      approved.length === 0
        ? 'No findings have completed formal reviewer sign-off.'
        : approved
            .map(
              (f: any, idx: number) =>
                `   [${idx + 1}] ${f.title} (${f.kind.toUpperCase()})\n       Confidence: ${(
                  f.confidence * 100
                ).toFixed(0)}%\n       Assessment: ${f.description}\n       Evidence Cited: ${
                  f.evidence_refs.join(', ') || 'Direct observation'
                }`
            )
            .join('\n\n'),
      ``,
      `3. ACTIVE WORKING HYPOTHESES & UNRESOLVED EVIDENCE (${pending.length}):`,
      pending.length === 0
        ? 'All working hypotheses have completed review.'
        : pending
            .map(
              (f: any, idx: number) =>
                `   [P-${idx + 1}] ${f.title} [Status: ${f.reviewer_status}]\n       ${f.description}`
            )
            .join('\n\n'),
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
    a.download = `VEGA-DEFENCE-SITREP-${currentCase.title.replace(/\s+/g, '_')}-${Date.now()}.md`
    a.click()
    URL.revokeObjectURL(url)
    notify('SITREP dossier generated and downloaded')
  }

  return (
    <Section
      title="Investigations &amp; Case Management"
      sub="Conduct structured intelligence investigations: record hypotheses, link supporting evidence, evaluate under commander review, and generate SITREP reports."
      actions={
        <div className="row gap8">
          <button
            className="btn primary"
            onClick={() => {
              setCreating((v) => !v)
              setParams({ create: 'true' })
            }}
          >
            <IcPlus size={14} /> New Investigation
          </button>
        </div>
      }
    >
      <SyntheticBanner />

      {/* Creation Modal / Inline Drawer */}
      {creating && (
        <Card
          title="Create New Investigation Dossier"
          style={{ marginBottom: 14, borderLeft: '3px solid var(--accent)' }}
          actions={
            <button className="btn sm ghost" onClick={() => setCreating(false)}>
              Cancel
            </button>
          }
        >
          <div className="grid g2">
            <div className="field">
              <label className="label">Investigation Title</label>
              <input
                className="input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Northern Theatre Airbase Readiness &amp; Chokepoint Review"
              />
            </div>
            <div className="field">
              <label className="label">Classification Level</label>
              <select
                className="input"
                value={classification}
                onChange={(e) => setClassification(e.target.value)}
              >
                <option value="INTERNAL">INTERNAL (Authorized Analysts)</option>
                <option value="RESTRICTED">RESTRICTED (Clearance Required)</option>
                <option value="PROTECTED">PROTECTED (Command Staff Only)</option>
              </select>
            </div>
          </div>
          <div className="field">
            <label className="label">Scope &amp; Strategic Objective</label>
            <textarea
              className="input"
              rows={2}
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              placeholder="What specific intelligence question or tactical vulnerability does this case address?"
            />
          </div>
          <div className="row gap8" style={{ marginTop: 8 }}>
            <button
              className="btn primary"
              disabled={createMutation.isPending || !title.trim()}
              onClick={() => createMutation.mutate()}
            >
              {createMutation.isPending ? 'Creating Dossier…' : 'Initialize Investigation'}
            </button>
            <button className="btn" onClick={() => setCreating(false)}>
              Cancel
            </button>
          </div>
        </Card>
      )}

      {/* Main Investigation Workspace */}
      <div className="grid g-1-2">
        {/* Left: Active Investigations List */}
        <Card
          title="Active Investigations"
          actions={<span className="tiny muted">{cases.data?.length ?? 0}</span>}
          bodyStyle={{ padding: 0 }}
        >
          {cases.isLoading ? (
            <Spinner />
          ) : (
            <div>
              {(cases.data ?? []).map((cs) => (
                <button
                  key={cs.id}
                  onClick={() => {
                    setActiveId(cs.id)
                    setParams({ caseId: cs.id, tab: activeTab })
                  }}
                  style={{
                    display: 'block',
                    width: '100%',
                    textAlign: 'left',
                    padding: '11px 13px',
                    background: activeId === cs.id ? 'var(--panel-2)' : 'transparent',
                    border: 'none',
                    borderBottom: '1px solid var(--line)',
                    borderLeft: `3px solid ${
                      activeId === cs.id ? 'var(--accent)' : 'transparent'
                    }`,
                    color: 'inherit',
                    cursor: 'pointer',
                  }}
                >
                  <div className="row between gap8">
                    <span style={{ fontSize: 12.5, fontWeight: 600 }}>{cs.title}</span>
                    <Badge tone={cs.status === 'in_review' ? 'amber' : 'blue'}>
                      {cs.status}
                    </Badge>
                  </div>
                  <div className="tiny muted" style={{ marginTop: 3 }}>
                    {cs.classification} · Officer: {cs.created_by?.split('@')[0]}
                  </div>
                </button>
              ))}
              {(cases.data ?? []).length === 0 && (
                <Empty>No active investigations. Click New Investigation to begin.</Empty>
              )}
            </div>
          )}
        </Card>

        {/* Right: Selected Investigation Dossier */}
        <div className="stack gap12">
          {!currentCase ? (
            <Card title="Investigation Dossier">
              <Empty>Select an investigation on the left to inspect evidence and findings.</Empty>
            </Card>
          ) : (
            <>
              {/* Dossier Tabs */}
              <div className="tabs" style={{ marginBottom: 4 }}>
                <button
                  className={`tab${activeTab === 'dossier' ? ' active' : ''}`}
                  onClick={() => setParams({ caseId: currentCase.id, tab: 'dossier' })}
                >
                  Dossier Overview
                </button>
                <button
                  className={`tab${activeTab === 'findings' ? ' active' : ''}`}
                  onClick={() => setParams({ caseId: currentCase.id, tab: 'findings' })}
                >
                  Findings &amp; Hypotheses ({findings.length})
                </button>
                <button
                  className={`tab${activeTab === 'review' ? ' active' : ''}`}
                  onClick={() => setParams({ caseId: currentCase.id, tab: 'review' })}
                >
                  Reviewer Decisions
                </button>
                <button
                  className={`tab${activeTab === 'reports' ? ' active' : ''}`}
                  onClick={() => setParams({ caseId: currentCase.id, tab: 'reports' })}
                >
                  <IcReport size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                  SITREP &amp; Reports
                </button>
              </div>

              {/* TAB 1: DOSSIER OVERVIEW */}
              {activeTab === 'dossier' && (
                <Card
                  title={currentCase.title}
                  actions={
                    <div className="row gap6">
                      <Badge tone="blue">{currentCase.classification}</Badge>
                      <Badge tone={currentCase.status === 'in_review' ? 'amber' : 'green'}>
                        {currentCase.status}
                      </Badge>
                    </div>
                  }
                >
                  <div style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.6 }}>
                    {currentCase.description || 'No strategic scope recorded.'}
                  </div>

                  <dl className="kv" style={{ marginTop: 14 }}>
                    <dt>Case ID</dt>
                    <dd className="mono tiny">{currentCase.id}</dd>
                    <dt>Officer of Record</dt>
                    <dd>{currentCase.created_by}</dd>
                    <dt>Created Date</dt>
                    <dd>{fmtDate(currentCase.created_at)}</dd>
                    <dt>Status</dt>
                    <dd className="tiny font-medium">{currentCase.status.toUpperCase()}</dd>
                  </dl>

                  <div className="hr" />
                  <div className="row between">
                    <span className="tiny muted">
                      {findings.length} findings recorded · {findings.filter((f: any) => f.reviewer_status === 'approved').length} approved by reviewer
                    </span>
                    <button className="btn sm primary" onClick={generateSITREP}>
                      <IcDownload size={13} /> Export SITREP (Markdown)
                    </button>
                  </div>
                </Card>
              )}

              {/* TAB 2: FINDINGS & HYPOTHESES */}
              {activeTab === 'findings' && (
                <div className="stack gap12">
                  <Card title="Record Analytical Finding or Hypothesis">
                    <div className="grid g2">
                      <div className="field">
                        <label className="label">Finding Title</label>
                        <input
                          className="input"
                          value={fTitle}
                          onChange={(e) => setFTitle(e.target.value)}
                          placeholder="e.g. Forward fuel reserve concentration vulnerability"
                        />
                      </div>
                      <div className="field">
                        <label className="label">Analytical Kind</label>
                        <select
                          className="input"
                          value={fKind}
                          onChange={(e) => setFKind(e.target.value)}
                        >
                          <option value="evidence">Verified Evidence (Observed fact)</option>
                          <option value="hypothesis">Working Hypothesis (Under test)</option>
                          <option value="assumption">Operational Assumption (Unverified)</option>
                          <option value="conclusion">Assessment Conclusion</option>
                        </select>
                      </div>
                    </div>
                    <div className="field">
                      <label className="label">Assessment &amp; Supporting Context</label>
                      <textarea
                        className="input"
                        rows={2}
                        value={fDesc}
                        onChange={(e) => setFDesc(e.target.value)}
                        placeholder="Detail the tactical observation, anomaly, or rationale…"
                      />
                    </div>
                    <div className="row between" style={{ marginTop: 8 }}>
                      <span className="tiny muted">
                        {KIND_HINT[fKind]?.desc}
                      </span>
                      <button
                        className="btn primary"
                        disabled={addFinding.isPending || !fTitle.trim()}
                        onClick={() => addFinding.mutate()}
                      >
                        {addFinding.isPending ? 'Recording…' : 'Record Finding'}
                      </button>
                    </div>
                  </Card>

                  {/* Findings list */}
                  <Card title={`Recorded Findings (${findings.length})`}>
                    <div className="stack gap8">
                      {findings.map((f: any, idx: number) => (
                        <div
                          key={f.id}
                          style={{
                            padding: '10px 12px',
                            border: '1px solid var(--line)',
                            borderRadius: 3,
                            background: 'var(--panel-2)',
                          }}
                        >
                          <div className="row between">
                            <div className="row gap6">
                              <Badge tone={KIND_HINT[f.kind]?.tone ?? 'neutral'}>
                                {f.kind.toUpperCase()}
                              </Badge>
                              <span style={{ fontSize: 13, fontWeight: 600 }}>{f.title}</span>
                            </div>
                            <Badge
                              tone={
                                f.reviewer_status === 'approved'
                                  ? 'green'
                                  : f.reviewer_status === 'rejected'
                                  ? 'red'
                                  : 'amber'
                              }
                            >
                              {f.reviewer_status}
                            </Badge>
                          </div>
                          <div className="tiny dim" style={{ marginTop: 4, lineHeight: 1.5 }}>
                            {f.description}
                          </div>
                          <div className="row between" style={{ marginTop: 6 }}>
                            <span className="tiny muted">
                              Confidence: {(f.confidence * 100).toFixed(0)}% · Author: {f.created_by}
                            </span>
                            {canReview && f.reviewer_status !== 'approved' && (
                              <button
                                className="btn sm ghost"
                                onClick={() => reviewMutation.mutate({ fid: f.id, decision: 'approved' })}
                              >
                                Sign off as Reviewer
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                      {findings.length === 0 && (
                        <Empty>No findings recorded yet in this investigation.</Empty>
                      )}
                    </div>
                  </Card>
                </div>
              )}

              {/* TAB 3: REVIEW & APPROVAL */}
              {activeTab === 'review' && (
                <Card title="Commander &amp; Reviewer Evaluation">
                  <div className="stack gap8">
                    {!canReview && (
                      <div className="banner warn">
                        Reviewer approval requires Flag Officer, Operations Reviewer, or Command Administrator role.
                      </div>
                    )}
                    {findings.map((f: any) => (
                      <div
                        key={f.id}
                        style={{
                          padding: '11px 13px',
                          border: '1px solid var(--line)',
                          borderRadius: 3,
                        }}
                      >
                        <div className="row between">
                          <span style={{ fontSize: 13, fontWeight: 600 }}>{f.title}</span>
                          <Badge tone={f.reviewer_status === 'approved' ? 'green' : 'amber'}>
                            {f.reviewer_status}
                          </Badge>
                        </div>
                        <div className="tiny dim" style={{ marginTop: 3 }}>
                          {f.description}
                        </div>
                        {canReview && (
                          <div className="row gap6" style={{ marginTop: 10 }}>
                            <button
                              className="btn sm primary"
                              onClick={() => reviewMutation.mutate({ fid: f.id, decision: 'approved' })}
                            >
                              Approve Finding
                            </button>
                            <button
                              className="btn sm"
                              onClick={() => reviewMutation.mutate({ fid: f.id, decision: 'rejected' })}
                            >
                              Reject
                            </button>
                            <button
                              className="btn sm ghost"
                              onClick={() => reviewMutation.mutate({ fid: f.id, decision: 'needs_revision' })}
                            >
                              Request Changes
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* TAB 4: SITREP & REPORTS */}
              {activeTab === 'reports' && (
                <div className="stack gap12">
                  <Card
                    title="Operational SITREP Generation"
                    actions={
                      <button className="btn primary" onClick={generateSITREP}>
                        <IcDownload size={13} /> Download SITREP Dossier (.md)
                      </button>
                    }
                  >
                    <div className="stack gap8">
                      <div className="tiny dim">
                        Generate an evidence-grounded military situation report citing all reviewed findings,
                        unresolved working hypotheses, and chain-of-custody timestamps.
                      </div>
                      <div className="hr" />
                      <div className="grid g3">
                        <div className="card" style={{ padding: 10 }}>
                          <span className="tiny muted">Case File</span>
                          <div style={{ fontWeight: 600, marginTop: 3 }}>{currentCase.title}</div>
                        </div>
                        <div className="card" style={{ padding: 10 }}>
                          <span className="tiny muted">Approved Findings</span>
                          <div style={{ fontWeight: 600, marginTop: 3, color: 'var(--green)' }}>
                            {findings.filter((f: any) => f.reviewer_status === 'approved').length}
                          </div>
                        </div>
                        <div className="card" style={{ padding: 10 }}>
                          <span className="tiny muted">Pending Hypotheses</span>
                          <div style={{ fontWeight: 600, marginTop: 3, color: 'var(--amber)' }}>
                            {findings.filter((f: any) => f.reviewer_status !== 'approved').length}
                          </div>
                        </div>
                      </div>
                    </div>
                  </Card>

                  {/* Central Report Generation component embedded */}
                  <Reports />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </Section>
  )
}
