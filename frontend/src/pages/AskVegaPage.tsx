import { useRef, useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { api, type AIResult, type SearchHit } from '../api'
import { Badge, Card, Empty, ErrorBox, Section, Spinner, SyntheticBanner } from '../components/ui'
import { IcAI, IcSearch } from '../components/icons'
import { useUI } from '../store'

const SUGGESTED_QUESTIONS = [
  'What is the operational readiness and radar coverage of Forward Airbase Trishul?',
  'Summarise the tactical status of Strategic River Crossing Bridge Mahanadi-03.',
  'Which forward installations are supplied by Central Ammunition Depot CAD-09?',
  'Explain the logistics and supply chain evidence for Strategic POL Depot SP-04.',
  'Summarise the findings of the Northern Sector Readiness Assessment.',
]

const SEARCH_KINDS = ['', 'entity', 'document', 'case']
const SEARCH_SUGGESTIONS = [
  'Forward Airbase Trishul',
  'Radar Indra-II coverage',
  'Ammunition Depot CAD-09',
  'Strategic POL Depot',
  'Bridge Mahanadi-03',
]
const HISTORY_KEY = 'vega-search-history'

function renderAnswerWithCitations(text: string) {
  const parts = text.split(/(\[E\d+\])/g)
  return parts.map((p, i) => {
    if (/^\[E\d+\]$/.test(p)) {
      return (
        <span
          key={i}
          className="badge accent"
          style={{ margin: '0 3px', fontWeight: 600, cursor: 'pointer' }}
        >
          {p}
        </span>
      )
    }
    return <span key={i}>{p}</span>
  })
}

export default function AskVegaPage() {
  const [params, setParams] = useSearchParams()
  const activeTab = (params.get('tab') as 'ask' | 'search') || 'ask'
  const initialQ = params.get('q') || ''
  const openPanel = useUI((s) => s.openPanel)

  // ----------------------------------------------------
  // ASK VEGA STATE
  // ----------------------------------------------------
  const [question, setQuestion] = useState(activeTab === 'ask' ? initialQ : '')
  const [caseContextId, setCaseContextId] = useState('')
  const [thread, setThread] = useState<{ q: string; r: AIResult }[]>([])
  const endRef = useRef<HTMLDivElement>(null)

  const cases = useQuery({ queryKey: ['cases'], queryFn: () => api.get<any[]>('/cases') })
  const config = useQuery({ queryKey: ['ai-config'], queryFn: () => api.get<any>('/ai/config') })

  const askMutation = useMutation({
    mutationFn: (qText: string) =>
      api.post<AIResult>('/ai/ask', { question: qText, case_id: caseContextId || null }),
    onSuccess: (r, qText) => {
      setThread((t) => [...t, { q: qText, r }])
      setQuestion('')
      setTimeout(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), 80)
    },
  })

  // ----------------------------------------------------
  // ADVANCED SEARCH STATE
  // ----------------------------------------------------
  const [searchQuery, setSearchQuery] = useState(activeTab === 'search' ? initialQ : '')
  const [searchKind, setSearchKind] = useState('')
  const [searchSubmitted, setSearchSubmitted] = useState(initialQ)

  const searchResults = useQuery({
    queryKey: ['search', searchSubmitted, searchKind],
    queryFn: () =>
      api.get<{ results: SearchHit[]; count: number }>(
        `/search?q=${encodeURIComponent(searchSubmitted)}${searchKind ? `&kind=${searchKind}` : ''}&limit=40`
      ),
    enabled: searchSubmitted.trim().length > 0,
  })

  function runSearch(term: string) {
    setSearchQuery(term)
    setSearchSubmitted(term)
    setParams({ tab: 'search', q: term })
    try {
      const hist = JSON.parse(localStorage.getItem(HISTORY_KEY) ?? '[]') as string[]
      const next = [term, ...hist.filter((h) => h !== term)].slice(0, 8)
      localStorage.setItem(HISTORY_KEY, JSON.stringify(next))
    } catch {}
  }

  const searchHistory: string[] = (() => {
    try {
      return JSON.parse(localStorage.getItem(HISTORY_KEY) ?? '[]')
    } catch {
      return []
    }
  })()

  // Sync url param if tab changes or q param provided
  useEffect(() => {
    if (initialQ && activeTab === 'search') {
      setSearchSubmitted(initialQ)
    }
  }, [initialQ, activeTab])

  return (
    <Section
      title="Ask VEGA &amp; Universal Search"
      sub="One unified intelligence gateway. Query authorised records using natural language or conduct structured lexical searches."
      actions={
        <Badge tone={config.data?.external_model_configured ? 'green' : 'blue'}>
          {config.data?.external_model_configured
            ? 'External LLM Configured'
            : 'Deterministic Grounded Composer'}
        </Badge>
      }
    >
      <SyntheticBanner />

      <div className="tabs">
        <button
          className={`tab${activeTab === 'ask' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'ask' })}
        >
          <IcAI size={14} style={{ display: 'inline', marginRight: 5, verticalAlign: 'middle' }} />
          Ask VEGA (AI Intelligence Co-Pilot)
        </button>
        <button
          className={`tab${activeTab === 'search' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'search' })}
        >
          <IcSearch size={14} style={{ display: 'inline', marginRight: 5, verticalAlign: 'middle' }} />
          Advanced Search ({searchResults.data?.count ?? 0} matches)
        </button>
      </div>

      {/* -------------------- TAB 1: ASK VEGA -------------------- */}
      {activeTab === 'ask' && (
        <div className="grid g-2-1">
          <div className="stack gap12">
            <Card
              title="What would you like to understand?"
              actions={
                <select
                  className="input"
                  style={{ width: 230, fontSize: 11.5 }}
                  value={caseContextId}
                  onChange={(e) => setCaseContextId(e.target.value)}
                  aria-label="Scope to investigation context"
                >
                  <option value="">No investigation context</option>
                  {(cases.data ?? []).map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title}
                    </option>
                  ))}
                </select>
              }
            >
              <form
                className="row gap8"
                onSubmit={(e) => {
                  e.preventDefault()
                  if (question.trim()) askMutation.mutate(question.trim())
                }}
              >
                <input
                  className="input"
                  placeholder="Ask VEGA anything about your available information…"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  style={{ padding: '9px 12px', fontSize: 13 }}
                  autoFocus
                />
                <button
                  className="btn primary"
                  disabled={askMutation.isPending || !question.trim()}
                  type="submit"
                  style={{ padding: '9px 16px' }}
                >
                  {askMutation.isPending ? (
                    <>
                      <span className="spinner" /> Retrieving…
                    </>
                  ) : (
                    'Ask'
                  )}
                </button>
              </form>

              <div className="eyebrow" style={{ marginTop: 14, marginBottom: 6 }}>
                Suggested inquiries
              </div>
              <div className="row gap6" style={{ flexWrap: 'wrap' }}>
                {SUGGESTED_QUESTIONS.map((sq) => (
                  <button
                    key={sq}
                    className="btn sm ghost"
                    onClick={() => askMutation.mutate(sq)}
                    style={{
                      maxWidth: '100%',
                      whiteSpace: 'normal',
                      textAlign: 'left',
                      lineHeight: 1.4,
                      padding: '4px 8px',
                    }}
                  >
                    {sq}
                  </button>
                ))}
              </div>

              {askMutation.error && (
                <div style={{ marginTop: 12 }}>
                  <ErrorBox error={askMutation.error} />
                </div>
              )}
            </Card>

            {thread.length === 0 && (
              <Card title="Grounded Analytical Environment">
                <Empty>
                  Enter an inquiry or select a suggested question above. Answers are composed exclusively
                  from records you have clearance to inspect. When evidence is insufficient, the assistant
                  formally refuses rather than speculating.
                </Empty>
              </Card>
            )}

            {thread.map((t, idx) => (
              <div key={idx} className="assistant-msg">
                <div className="row between gap8" style={{ marginBottom: 10 }}>
                  <span style={{ fontSize: 13.5, fontWeight: 600 }}>{t.q}</span>
                  <Badge tone={t.r.insufficient_evidence ? 'red' : 'green'}>
                    {t.r.insufficient_evidence
                      ? 'insufficient evidence (refused)'
                      : `confidence ${(t.r.confidence * 100).toFixed(0)}%`}
                  </Badge>
                </div>

                {/* Structured Answer Layout */}
                <div style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--text)' }}>
                  {renderAnswerWithCitations(t.r.answer)}
                </div>

                <div className="hr" style={{ margin: '12px 0 8px' }} />

                {/* Citations & Evidence */}
                <div className="eyebrow" style={{ marginBottom: 6 }}>
                  Supporting Citations ({t.r.citations.length}) — Click to Inspect
                </div>
                <div className="row gap6" style={{ flexWrap: 'wrap' }}>
                  {t.r.citations.map((c) => (
                    <button
                      key={c.id}
                      className="cite"
                      onClick={() =>
                        openPanel({
                          kind: `${c.kind.toUpperCase()} · ${c.id}`,
                          title: c.title,
                          data: (
                            <div className="stack gap8">
                              <div className="tiny dim">{c.snippet}</div>
                              <dl className="kv">
                                <dt>Entity Kind</dt>
                                <dd>{c.kind}</dd>
                                <dt>Clearance</dt>
                                <dd className="badge blue">INTERNAL</dd>
                                <dt>Audit Citation</dt>
                                <dd className="mono tiny">{c.id}</dd>
                              </dl>
                            </div>
                          ),
                        })
                      }
                    >
                      <span className="dot teal" />
                      <span className="tiny font-medium">{c.title}</span>
                    </button>
                  ))}
                  {t.r.citations.length === 0 && (
                    <span className="tiny muted">No citation records attached.</span>
                  )}
                </div>

                {/* Data Limitations Notice */}
                <div
                  className="banner"
                  style={{
                    marginTop: 12,
                    fontSize: 11,
                    background: 'var(--panel-2)',
                    borderColor: 'var(--line)',
                  }}
                >
                  <span className="badge neutral" style={{ flex: '0 0 auto' }}>
                    Audit Notice
                  </span>
                  <span>
                    Answer grounded in deterministic index search. Unverified working hypotheses are
                    marked accordingly and require reviewer sign-off before tactical decisions.
                  </span>
                </div>
              </div>
            ))}
            <div ref={endRef} />
          </div>

          <div className="stack gap12">
            <Card title="Grounded Retrieval Discipline">
              <div className="stack gap8 tiny muted">
                <div>
                  <strong>Tenant Scoped</strong>: Retrieval strictly checks your active organization
                  boundaries and clearance ceiling.
                </div>
                <div>
                  <strong>Mandatory Citations</strong>: Every substantive claim links to a verified
                  record in the sovereign graph.
                </div>
                <div>
                  <strong>Safe Refusal</strong>: Questions lacking sufficient evidence are refused to
                  prevent speculation.
                </div>
              </div>
            </Card>

            <Card title="Recent Inquiries">
              <div className="stack gap6">
                {thread.slice(-4).map((th, i) => (
                  <button
                    key={i}
                    className="btn sm ghost"
                    style={{ textAlign: 'left', width: '100%', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
                    onClick={() => setQuestion(th.q)}
                  >
                    {th.q}
                  </button>
                ))}
                {thread.length === 0 && <span className="tiny muted">Inquiries in this session will appear here.</span>}
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* -------------------- TAB 2: ADVANCED SEARCH -------------------- */}
      {activeTab === 'search' && (
        <div className="stack gap12">
          <form
            className="row gap8"
            onSubmit={(e) => {
              e.preventDefault()
              if (searchQuery.trim()) runSearch(searchQuery.trim())
            }}
          >
            <div className="searchbox" style={{ maxWidth: 640 }}>
              <input
                className="input"
                placeholder="Search across all entities, documents and cases…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                autoFocus
              />
            </div>
            <select
              className="input"
              style={{ width: 160 }}
              value={searchKind}
              onChange={(e) => setSearchKind(e.target.value)}
              aria-label="Result kind"
            >
              {SEARCH_KINDS.map((k) => (
                <option key={k} value={k}>
                  {k ? k.toUpperCase() : 'All Result Kinds'}
                </option>
              ))}
            </select>
            <button className="btn primary" type="submit">
              Search
            </button>
          </form>

          {/* Search suggestions & history chips */}
          <div className="row gap8" style={{ flexWrap: 'wrap' }}>
            <span className="tiny muted">Suggested:</span>
            {SEARCH_SUGGESTIONS.map((s) => (
              <button
                key={s}
                className="btn sm ghost"
                onClick={() => runSearch(s)}
              >
                {s}
              </button>
            ))}
            {searchHistory.length > 0 && (
              <>
                <span className="tiny muted" style={{ marginLeft: 8 }}>History:</span>
                {searchHistory.slice(0, 4).map((h) => (
                  <button
                    key={h}
                    className="btn sm ghost"
                    onClick={() => runSearch(h)}
                  >
                    {h}
                  </button>
                ))}
              </>
            )}
          </div>

          {/* Search Results */}
          <Card
            title={
              searchSubmitted
                ? `Results for "${searchSubmitted}" (${searchResults.data?.count ?? 0} matches)`
                : 'Universal Search'
            }
          >
            {searchResults.isLoading ? (
              <Spinner label="Searching indexed records…" />
            ) : searchResults.error ? (
              <ErrorBox error={searchResults.error} />
            ) : !searchSubmitted ? (
              <Empty>Enter a query above to search across entities, documents, and cases.</Empty>
            ) : (searchResults.data?.results ?? []).length === 0 ? (
              <Empty>No authorized records match this search query.</Empty>
            ) : (
              <div className="stack gap8">
                {(searchResults.data?.results ?? []).map((hit) => (
                  <div
                    key={`${hit.kind}-${hit.id}`}
                    style={{
                      padding: '10px 12px',
                      border: '1px solid var(--line)',
                      borderRadius: 3,
                      background: 'var(--panel-2)',
                    }}
                  >
                    <div className="row between gap8">
                      <div className="row gap6">
                        <Badge tone="neutral">{hit.kind.toUpperCase()}</Badge>
                        <span style={{ fontSize: 13, fontWeight: 600 }}>{hit.title}</span>
                      </div>
                      <span className="tiny mono muted">{hit.id.slice(0, 8)}…</span>
                    </div>
                    <div className="tiny dim" style={{ marginTop: 4 }}>
                      {hit.snippet}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}
    </Section>
  )
}
