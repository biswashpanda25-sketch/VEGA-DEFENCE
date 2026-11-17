import { useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { api, type AIResult } from '../api'
import { Badge, Card, Empty, ErrorBox, Section, Spinner } from '../components/ui'
import { useUI } from '../store'

const EXAMPLES = [
  'What is the operational readiness and radar coverage of Forward Airbase Trishul?',
  'Summarise the tactical status of Strategic River Crossing Bridge Mahanadi-03.',
  'Which forward installations are supplied by Central Ammunition Depot CAD-09?',
  'Explain the logistics and supply chain evidence for Strategic POL Depot SP-04.',
  'Summarise the findings of the Northern Sector Readiness Assessment.',
]

function renderAnswer(text: string) {
  const parts = text.split(/(\[E\d+\])/g)
  return parts.map((p, i) => {
    if (/^\[E\d+\]$/.test(p)) return <span key={i} className="badge accent" style={{ margin: '0 2px' }}>{p}</span>
    return <span key={i}>{p}</span>
  })
}

export default function Assistant() {
  const [q, setQ] = useState('')
  const [caseId, setCaseId] = useState('')
  const [thread, setThread] = useState<{ q: string; r: AIResult }[]>([])
  const endRef = useRef<HTMLDivElement>(null)
  const openPanel = useUI((s) => s.openPanel)

  const cases = useQuery({ queryKey: ['cases'], queryFn: () => api.get<any[]>('/cases') })
  const config = useQuery({ queryKey: ['ai-config'], queryFn: () => api.get<any>('/ai/config') })
  const history = useQuery({ queryKey: ['ai-history'], queryFn: () => api.get<any[]>('/ai/history') })

  const ask = useMutation({
    mutationFn: (question: string) => api.post<AIResult>('/ai/ask', { question, case_id: caseId || null }),
    onSuccess: (r, question) => {
      setThread((t) => [...t, { q: question, r }])
      setQ('')
      setTimeout(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), 60)
    },
  })

  return (
    <Section
      title="AI Tactical Intelligence Assistant"
      sub="Retrieval-grounded military decision support. Answers are composed only from authorized defence records with strict cryptographic and clearance boundaries."
      actions={<Badge tone={config.data?.external_model_configured ? 'green' : 'blue'}>
        {config.data?.external_model_configured ? 'external model' : 'deterministic grounded composer'}
      </Badge>}
    >
      <div className="grid g-2-1">
        <div className="stack gap12">
          <Card title="Ask the assistant" actions={
            <select className="input" style={{ width: 220, fontSize: 11.5 }} value={caseId} onChange={(e) => setCaseId(e.target.value)} aria-label="Case context">
              <option value="">No case context</option>
              {(cases.data ?? []).map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
            </select>
          }>
            <form className="row gap8" onSubmit={(e) => { e.preventDefault(); if (q.trim()) ask.mutate(q.trim()) }}>
              <input className="input" placeholder="Ask about tactical installations, order of battle, or readiness records…" value={q} onChange={(e) => setQ(e.target.value)} />
              <button className="btn primary" disabled={ask.isPending || !q.trim()}>
                {ask.isPending ? <><span className="spinner" /> Retrieving…</> : 'Ask'}
              </button>
            </form>
            <div className="row gap6" style={{ marginTop: 9, flexWrap: 'wrap' }}>
              {EXAMPLES.map((e) => (
                <button key={e} className="btn sm ghost" onClick={() => ask.mutate(e)} style={{ maxWidth: '100%', whiteSpace: 'normal', textAlign: 'left' }}>{e}</button>
              ))}
            </div>
            {ask.error && <div style={{ marginTop: 10 }}><ErrorBox error={ask.error} /></div>}
          </Card>

          {thread.length === 0 && (
            <Card title="No conversation yet">
              <Empty>Ask a question to begin. The assistant will refuse when evidence is insufficient rather than speculate.</Empty>
            </Card>
          )}

          {thread.map((t, i) => (
            <div key={i} className="assistant-msg">
              <div className="row between gap8" style={{ marginBottom: 8 }}>
                <span style={{ fontSize: 12.5, fontWeight: 600 }}>{t.q}</span>
                <div className="row gap6">
                  <Badge tone={t.r.insufficient_evidence ? 'red' : 'green'}>
                    {t.r.insufficient_evidence ? 'insufficient evidence' : `confidence ${(t.r.confidence * 100).toFixed(0)}%`}
                  </Badge>
                </div>
              </div>
              <div style={{ fontSize: 12.5, lineHeight: 1.7, color: 'var(--text)' }}>{renderAnswer(t.r.answer)}</div>
              <div className="hr" />
              <div className="eyebrow" style={{ marginBottom: 6 }}>Citations — {t.r.citations.length}</div>
              <div className="row gap6" style={{ flexWrap: 'wrap' }}>
                {t.r.citations.map((c) => (
                  <button key={c.id} className="cite" onClick={() => openPanel({
                    kind: `${c.kind.toUpperCase()} · ${c.id}`,
                    title: c.title,
                    data: (<div className="stack gap8">
                      <div className="tiny dim">{c.snippet}</div>
                      <dl className="kv">
                        <dt>Kind</dt><dd>{c.kind}</dd>
                        <dt>Record</dt><dd className="mono tiny" style={{ wordBreak: 'break-all' }}>{c.record_id}</dd>
                        <dt>Classification</dt><dd>{c.classification}</dd>
                        <dt>Synthetic</dt><dd>{c.synthetic ? 'yes' : 'no'}</dd>
                        <dt>Relevance</dt><dd>{c.score.toFixed(2)}</dd>
                      </dl>
                    </div>),
                  })}>
                    <strong>{c.id}</strong> {c.title.length > 30 ? c.title.slice(0, 30) + '…' : c.title}
                  </button>
                ))}
              </div>
              <div className="tiny muted" style={{ marginTop: 9 }}>
                prompt {t.r.meta.prompt_version} · provider {t.r.meta.provider} · retrieved {t.r.meta.retrieved} records
                {t.r.meta.model_invoked ? ' · external model output verified for citation coverage' : ' · composed deterministically from retrieved records'}
              </div>
            </div>
          ))}
          <div ref={endRef} />
        </div>

        <div className="stack gap12">
          <Card title="Grounding policy">
            <div className="stack gap8 tiny muted">
              <div>• Retrieval is scoped to your organization and role before any text is generated.</div>
              <div>• Imported documents are treated as untrusted data; embedded instructions are never executed.</div>
              <div>• Answers without at least one citation are rejected and replaced by the grounded composer.</div>
              <div>• Inferences are labelled as such; the assistant never upgrades them to fact.</div>
              <div>• The assistant cannot change permissions, exfiltrate data or trigger workflows.</div>
            </div>
          </Card>
          <Card title="Recent queries" bodyStyle={{ padding: 0 }}>
            {history.isLoading ? <Spinner /> : (
              <div>
                {(history.data ?? []).slice(0, 6).map((h) => (
                  <div key={h.id} style={{ padding: '8px 11px', borderBottom: '1px solid var(--line)' }}>
                    <div className="tiny">{h.question}</div>
                    <div className="tiny muted">{h.citations.length} citation(s)</div>
                  </div>
                ))}
                {(history.data ?? []).length === 0 && <Empty>No history</Empty>}
              </div>
            )}
          </Card>
        </div>
      </div>
    </Section>
  )
}
