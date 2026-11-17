import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { api, type SearchHit } from '../api'
import { Badge, Card, Empty, ErrorBox, Section, Spinner } from '../components/ui'

const KINDS = ['', 'entity', 'document', 'case']
const SUGGESTIONS = ['Forward Airbase Trishul', 'Radar Indra-II coverage', 'Ammunition Depot CAD-09', 'Strategic POL Depot', 'Strategic River Crossing']
const HISTORY_KEY = 'vega-search-history'

export default function SearchPage() {
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const [kind, setKind] = useState('')
  const [input, setInput] = useState(q)

  const results = useQuery({
    queryKey: ['search', q, kind],
    queryFn: () => api.get<{ results: SearchHit[]; count: number }>(`/search?q=${encodeURIComponent(q)}${kind ? `&kind=${kind}` : ''}&limit=40`),
    enabled: q.trim().length > 0,
  })

  function run(term: string) {
    setInput(term)
    setParams({ q: term })
    try {
      const hist = JSON.parse(localStorage.getItem(HISTORY_KEY) ?? '[]') as string[]
      const next = [term, ...hist.filter((h) => h !== term)].slice(0, 8)
      localStorage.setItem(HISTORY_KEY, JSON.stringify(next))
    } catch { /* history is a convenience only */ }
  }

  const history: string[] = (() => {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY) ?? '[]') } catch { return [] }
  })()

  return (
    <Section
      title="Universal Search"
      sub="Lexical retrieval across entities, documents and cases. Results are filtered by your organization and role before ranking."
    >
      <form className="row gap8" style={{ marginBottom: 12 }}
        onSubmit={(e) => { e.preventDefault(); if (input.trim()) run(input.trim()) }}>
        <div className="searchbox" style={{ maxWidth: 620 }}>
          <input className="input" placeholder="Search authorized records…" value={input} onChange={(e) => setInput(e.target.value)} autoFocus />
        </div>
        <select className="input" style={{ width: 150 }} value={kind} onChange={(e) => setKind(e.target.value)} aria-label="Result kind">
          {KINDS.map((k) => <option key={k} value={k}>{k ? k : 'All kinds'}</option>)}
        </select>
        <button className="btn primary" type="submit">Search</button>
      </form>

      {!q && (
        <div className="grid g2">
          <Card title="Suggested queries">
            <div className="stack gap6">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="btn ghost" style={{ justifyContent: 'flex-start' }} onClick={() => run(s)}>{s}</button>
              ))}
            </div>
          </Card>
          <Card title="Recent searches" actions={<span className="tiny muted">stored locally</span>}>
            {history.length === 0 ? <Empty>No search history on this device</Empty> : (
              <div className="stack gap4">
                {history.map((h) => (
                  <button key={h} className="btn ghost sm" style={{ justifyContent: 'flex-start' }} onClick={() => run(h)}>{h}</button>
                ))}
              </div>
            )}
            <div className="tiny muted" style={{ marginTop: 8 }}>
              Search queries are also written to the audit log server-side, as required for institutional traceability.
            </div>
          </Card>
        </div>
      )}

      {q && (
        <>
          {results.error && <ErrorBox error={results.error} />}
          <Card title={`Results for “${q}”`} actions={<span className="tiny muted">{results.data?.count ?? 0} matches</span>} bodyStyle={{ padding: 0 }}>
            {results.isLoading ? <Spinner /> : results.data && results.data.results.length > 0 ? (
              results.data.results.map((r) => (
                <div key={`${r.kind}-${r.id}`} style={{ padding: '11px 13px', borderBottom: '1px solid var(--line)' }}>
                  <div className="row between gap8">
                    <span style={{ fontSize: 13 }}>{r.title}</span>
                    <div className="row gap6">
                      <Badge tone="neutral">{r.kind}</Badge>
                      <Badge tone={r.synthetic ? 'amber' : 'blue'}>{r.synthetic ? 'synthetic' : 'imported'}</Badge>
                      <span className="tiny mono muted">score {r.score.toFixed(2)}</span>
                    </div>
                  </div>
                  <div className="tiny dim" style={{ marginTop: 3 }}>{r.snippet}</div>
                </div>
              ))
            ) : <Empty>No authorized records matched this query. Try a broader term.</Empty>}
          </Card>
        </>
      )}
    </Section>
  )
}
