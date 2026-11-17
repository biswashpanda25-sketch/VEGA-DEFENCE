import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api'
import { Badge, Card, Empty, ErrorBox, Section, Spinner } from '../components/ui'
import { useUI } from '../store'

type Node = { id: string; label: string; type: string; district: string; status: string; confidence: number; created_at?: string }
type Edge = { id: string; source: string; target: string; type: string; provenance: string; confidence: number; evidence: string; created_at?: string }

const PROV_COLOR: Record<string, string> = {
  confirmed: '#5AA87A', imported: '#6D8CFF', inferred: '#D5A13C', unverified: '#D9534F',
}
const TYPE_COLOR: Record<string, string> = {
  organization: '#D5A13C', department: '#E5B552', asset: '#5FB3A1', vehicle: '#5AA87A',
  facility: '#A78BFA', warehouse: '#6D8CFF', inventory_item: '#8298AE', project: '#D9534F',
  supplier: '#94A3B8', document: '#8298AE', case: '#D5A13C', location: '#5AA87A',
}

export default function GraphPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ['graph'], queryFn: () => api.get<{ nodes: Node[]; edges: Edge[] }>('/graph?limit=250') })
  const [provFilter, setProvFilter] = useState<string>('')
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({})
  const [selected, setSelected] = useState<Node | null>(null)
  const [scale, setScale] = useState(1)
  const [offset, setOffset] = useState({ x: 0, y: 0 })
  const dragRef = useRef<{ x: number; y: number } | null>(null)
  const openPanel = useUI((s) => s.openPanel)

  // Advanced features state
  const [pathMode, setPathMode] = useState(false)
  const [sourceId, setSourceId] = useState<string>('')
  const [targetId, setTargetId] = useState<string>('')
  const [timelineMode, setTimelineMode] = useState(false)
  const [timelinePct, setTimelinePct] = useState(100)
  const [isPlaying, setIsPlaying] = useState(false)

  const W = 900, H = 560

  // Degree centrality calculation
  const nodeDegrees = useMemo(() => {
    const deg: Record<string, number> = {}
    ;(data?.edges ?? []).forEach((e) => {
      deg[e.source] = (deg[e.source] ?? 0) + 1
      deg[e.target] = (deg[e.target] ?? 0) + 1
    })
    return deg
  }, [data?.edges])

  // Filter nodes & edges with timeline and dropdowns
  const rawNodes = useMemo(() => (data?.nodes ?? []).filter((n) => !typeFilter || n.type === typeFilter), [data, typeFilter])
  const nodeIds = useMemo(() => new Set(rawNodes.map((n) => n.id)), [rawNodes])
  const rawEdges = useMemo(
    () => (data?.edges ?? []).filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target) && (!provFilter || e.provenance === provFilter)),
    [data, nodeIds, provFilter],
  )

  // Timeline filtering
  const edges = useMemo(() => {
    if (!timelineMode || timelinePct >= 100) return rawEdges
    const limit = Math.max(1, Math.floor((rawEdges.length * timelinePct) / 100))
    return rawEdges.slice(0, limit)
  }, [rawEdges, timelineMode, timelinePct])

  const nodes = useMemo(() => {
    if (!timelineMode || timelinePct >= 100) return rawNodes
    const activeIds = new Set<string>()
    edges.forEach((e) => { activeIds.add(e.source); activeIds.add(e.target) })
    return rawNodes.filter((n) => activeIds.has(n.id))
  }, [rawNodes, edges, timelineMode, timelinePct])

  // Shortest path calculation (BFS)
  const activePath = useMemo(() => {
    if (!pathMode || !sourceId || !targetId || sourceId === targetId) return null
    const adj: Record<string, { neighbor: string; edgeId: string }[]> = {}
    edges.forEach((e) => {
      if (!adj[e.source]) adj[e.source] = []
      if (!adj[e.target]) adj[e.target] = []
      adj[e.source].push({ neighbor: e.target, edgeId: e.id })
      adj[e.target].push({ neighbor: e.source, edgeId: e.id })
    })

    const queue: { node: string; pathNodes: string[]; pathEdges: string[] }[] = [{ node: sourceId, pathNodes: [sourceId], pathEdges: [] }]
    const visited = new Set<string>([sourceId])

    while (queue.length > 0) {
      const cur = queue.shift()!
      if (cur.node === targetId) {
        return { found: true, nodeSet: new Set(cur.pathNodes), edgeSet: new Set(cur.pathEdges), pathNodes: cur.pathNodes, pathEdges: cur.pathEdges }
      }
      for (const { neighbor, edgeId } of adj[cur.node] ?? []) {
        if (!visited.has(neighbor)) {
          visited.add(neighbor)
          queue.push({
            node: neighbor,
            pathNodes: [...cur.pathNodes, neighbor],
            pathEdges: [...cur.pathEdges, edgeId],
          })
        }
      }
    }
    return { found: false, nodeSet: new Set([sourceId, targetId]), edgeSet: new Set<string>(), pathNodes: [], pathEdges: [] }
  }, [pathMode, sourceId, targetId, edges])

  // Timeline auto-play timer
  useEffect(() => {
    if (!isPlaying) return
    const timer = setInterval(() => {
      setTimelinePct((prev) => {
        if (prev >= 100) {
          setIsPlaying(false)
          return 100
        }
        return prev + 5
      })
    }, 400)
    return () => clearInterval(timer)
  }, [isPlaying])

  // deterministic force-directed layout (Fruchterman–Reingold style), computed once per node set
  useEffect(() => {
    if (!rawNodes.length) return
    const n = rawNodes.length
    const pos: Record<string, { x: number; y: number }> = {}
    rawNodes.forEach((node, i) => {
      const a = (i / n) * Math.PI * 2
      pos[node.id] = { x: W / 2 + Math.cos(a) * 220, y: H / 2 + Math.sin(a) * 180 }
    })
    const k = Math.sqrt((W * H) / Math.max(n, 1)) * 0.65
    for (let iter = 0; iter < 240; iter++) {
      const disp: Record<string, { x: number; y: number }> = {}
      rawNodes.forEach((u) => { disp[u.id] = { x: 0, y: 0 } })
      for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
          const a = rawNodes[i].id, b = rawNodes[j].id
          let dx = pos[a].x - pos[b].x, dy = pos[a].y - pos[b].y
          let d = Math.hypot(dx, dy) || 0.01
          const rep = (k * k) / d
          dx /= d; dy /= d
          disp[a].x += dx * rep; disp[a].y += dy * rep
          disp[b].x -= dx * rep; disp[b].y -= dy * rep
        }
      }
      rawEdges.forEach((e) => {
        if (!pos[e.source] || !pos[e.target]) return
        let dx = pos[e.source].x - pos[e.target].x, dy = pos[e.source].y - pos[e.target].y
        const d = Math.hypot(dx, dy) || 0.01
        const att = (d * d) / k
        dx /= d; dy /= d
        disp[e.source].x -= dx * att; disp[e.source].y -= dy * att
        disp[e.target].x += dx * att; disp[e.target].y += dy * att
      })
      rawNodes.forEach((v) => {
        const d = Math.hypot(disp[v.id].x, disp[v.id].y) || 0.01
        const limit = Math.min(d, 26)
        pos[v.id].x = Math.min(W - 92, Math.max(92, pos[v.id].x + (disp[v.id].x / d) * limit))
        pos[v.id].y = Math.min(H - 46, Math.max(46, pos[v.id].y + (disp[v.id].y / d) * limit))
        pos[v.id].x += (W / 2 - pos[v.id].x) * 0.006
        pos[v.id].y += (H / 2 - pos[v.id].y) * 0.006
      })
    }
    setPositions(pos)
  }, [rawNodes, rawEdges])

  function handleNodeClick(n: Node) {
    if (pathMode) {
      if (!sourceId) {
        setSourceId(n.id)
      } else if (!targetId && n.id !== sourceId) {
        setTargetId(n.id)
      } else {
        setSourceId(n.id)
        setTargetId('')
      }
    }
    inspect(n)
  }

  async function inspect(n: Node) {
    setSelected(n)
    const detail = await api.get<any>(`/entities/${n.id}`)
    openPanel({
      kind: 'GRAPH EXPLORATION',
      title: detail.entity.name,
      data: (
        <div className="stack gap8">
          <div className="row gap6" style={{ flexWrap: 'wrap' }}>
            <Badge tone="neutral">{detail.entity.entity_type}</Badge>
            <Badge>{detail.entity.status}</Badge>
            <Badge tone="amber">synthetic</Badge>
            <Badge tone="blue">Degree: {nodeDegrees[n.id] ?? 0}</Badge>
          </div>
          <p className="tiny dim" style={{ margin: 0 }}>{detail.entity.description || 'No description recorded.'}</p>
          <div className="eyebrow" style={{ marginTop: 4 }}>Relationships ({detail.relationships.length})</div>
          {detail.relationships.map((r: any) => (
            <div key={r.id} className="evidence" style={{ borderLeftColor: PROV_COLOR[r.provenance] }}>
              <div className="row between gap6">
                <span className="tiny mono">{r.rel_type}</span>
                <Badge tone={r.provenance}>{r.provenance}</Badge>
              </div>
              <div className="tiny" style={{ marginTop: 3 }}>
                {r.source_id === n.id ? r.target_name : r.source_name}
              </div>
              <div className="tiny muted" style={{ marginTop: 2 }}>{r.evidence}</div>
              <div className="tiny muted mono" style={{ marginTop: 2 }}>{r.source_ref}</div>
            </div>
          ))}
          {detail.relationships.length === 0 && <Empty>No recorded relationships</Empty>}
        </div>
      ),
    })
  }

  if (isLoading) return <Spinner label="Building graph…" />
  if (error) return <ErrorBox error={error} />

  const types = Array.from(new Set((data?.nodes ?? []).map((n) => n.type))).sort()
  const topHubs = [...(data?.nodes ?? [])].sort((a, b) => (nodeDegrees[b.id] ?? 0) - (nodeDegrees[a.id] ?? 0)).slice(0, 5)

  return (
    <Section
      title="Knowledge Graph & Network Intelligence"
      sub="Interactive entity graph with shortest-path tracing, temporal timeline playback, and degree centrality analysis."
      actions={
        <div className="row gap6" style={{ flexWrap: 'wrap' }}>
          <button
            className={`btn sm ${pathMode ? 'primary' : ''}`}
            onClick={() => { setPathMode(!pathMode); if (pathMode) { setSourceId(''); setTargetId('') } }}
          >
            🧭 Pathfinding {pathMode ? 'ON' : 'OFF'}
          </button>
          <button
            className={`btn sm ${timelineMode ? 'primary' : ''}`}
            onClick={() => setTimelineMode(!timelineMode)}
          >
            🕒 Time Slider {timelineMode ? 'ON' : 'OFF'}
          </button>
          <select className="input" style={{ width: 140 }} value={provFilter} onChange={(e) => setProvFilter(e.target.value)} aria-label="Provenance filter">
            <option value="">All provenance</option>
            {Object.keys(PROV_COLOR).map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <select className="input" style={{ width: 130 }} value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} aria-label="Type filter">
            <option value="">All types</option>
            {types.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      }
    >
      {/* Pathfinding bar */}
      {pathMode && (
        <div className="banner" style={{ marginBottom: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <div className="row gap8" style={{ flex: 1 }}>
            <span className="tiny" style={{ fontWeight: 600 }}>Shortest Path:</span>
            <select className="input" style={{ width: 220, fontSize: 11.5 }} value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
              <option value="">Select Source Entity</option>
              {rawNodes.map((n) => <option key={n.id} value={n.id}>{n.label.slice(0, 26)}</option>)}
            </select>
            <span>➔</span>
            <select className="input" style={{ width: 220, fontSize: 11.5 }} value={targetId} onChange={(e) => setTargetId(e.target.value)}>
              <option value="">Select Target Entity</option>
              {rawNodes.map((n) => <option key={n.id} value={n.id}>{n.label.slice(0, 26)}</option>)}
            </select>
          </div>
          {activePath && (
            <div className="row gap6">
              {activePath.found ? (
                <Badge tone="green">Path found: {activePath.pathEdges.length} hops ({activePath.pathNodes.length} nodes)</Badge>
              ) : (
                <Badge tone="red">No connected path</Badge>
              )}
              <button className="btn sm" onClick={() => { setSourceId(''); setTargetId('') }}>Clear</button>
            </div>
          )}
        </div>
      )}

      {/* Timeline scrubber bar */}
      {timelineMode && (
        <div className="banner" style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="btn sm" onClick={() => setIsPlaying(!isPlaying)}>
            {isPlaying ? '⏸ Pause' : '▶ Play Timeline'}
          </button>
          <input
            type="range"
            min={10}
            max={100}
            value={timelinePct}
            onChange={(e) => setTimelinePct(Number(e.target.value))}
            style={{ flex: 1, accentColor: 'var(--accent)' }}
          />
          <span className="tiny mono" style={{ minWidth: 100, textAlign: 'right' }}>
            {edges.length} / {rawEdges.length} links ({timelinePct}%)
          </span>
        </div>
      )}

      <div className="grid g-2-1">
        <Card bodyStyle={{ padding: 0 }} title={`${nodes.length} nodes · ${edges.length} edges`}
          actions={
            <div className="row gap4">
              <button className="btn sm" onClick={() => setScale((s) => Math.min(2.5, s + 0.15))}>+</button>
              <button className="btn sm" onClick={() => setScale((s) => Math.max(0.4, s - 0.15))}>−</button>
              <button className="btn sm" onClick={() => { setScale(1); setOffset({ x: 0, y: 0 }) }}>Reset</button>
            </div>
          }>
          <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 560, background: 'var(--graph-bg)', cursor: dragRef.current ? 'grabbing' : 'grab', display: 'block' }}
            onMouseDown={(e) => { dragRef.current = { x: e.clientX - offset.x, y: e.clientY - offset.y } }}
            onMouseMove={(e) => { if (dragRef.current) setOffset({ x: e.clientX - dragRef.current.x, y: e.clientY - dragRef.current.y }) }}
            onMouseUp={() => { dragRef.current = null }}
            onMouseLeave={() => { dragRef.current = null }}>
            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--line-2)" />
              </marker>
              <marker id="arrow-active" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--accent)" />
              </marker>
            </defs>
            <g transform={`translate(${offset.x} ${offset.y}) scale(${scale})`}>
              {edges.map((e) => {
                const s = positions[e.source], t = positions[e.target]
                if (!s || !t) return null
                const inPath = activePath?.edgeSet?.has(e.id)
                const isDimmed = activePath && !inPath

                return (
                  <line key={e.id} x1={s.x} y1={s.y} x2={t.x} y2={t.y}
                    stroke={inPath ? 'var(--accent)' : (PROV_COLOR[e.provenance] ?? '#94a3b8')}
                    strokeOpacity={inPath ? 1 : isDimmed ? 0.08 : (e.provenance === 'confirmed' ? 0.75 : 0.55)}
                    strokeWidth={inPath ? 3 : (e.provenance === 'confirmed' ? 1.5 : 1)}
                    strokeDasharray={e.provenance === 'inferred' ? '4 3' : e.provenance === 'unverified' ? '2 3' : undefined}
                    markerEnd={inPath ? 'url(#arrow-active)' : 'url(#arrow)'} />
                )
              })}
              {nodes.map((n) => {
                const p = positions[n.id]
                if (!p) return null
                const deg = nodeDegrees[n.id] ?? 0
                const baseR = n.type === 'organization' ? 11 : 7.5
                const r = baseR + Math.min(deg * 0.8, 6)
                const isSel = selected?.id === n.id
                const inPath = activePath?.nodeSet?.has(n.id)
                const isDimmed = activePath && !inPath

                return (
                  <g key={n.id} transform={`translate(${p.x} ${p.y})`} onClick={() => handleNodeClick(n)} style={{ cursor: 'pointer', opacity: isDimmed ? 0.15 : 1 }}>
                    <circle r={r + (inPath ? 6 : isSel ? 4 : 0)} fill="transparent"
                      stroke={inPath ? 'var(--accent)' : isSel ? 'var(--accent)' : 'transparent'}
                      strokeWidth={inPath ? 2.5 : 1.5}
                      strokeDasharray={inPath ? '3 2' : undefined} />
                    <circle r={r} fill={TYPE_COLOR[n.type] ?? '#7d8b99'} fillOpacity={0.9} stroke="var(--bg-2)" strokeWidth={1.5} />
                    <text y={r + 12} textAnchor="middle" fontSize={8.5} fill="var(--text)" fontWeight={inPath ? '700' : '500'}
                      style={{ pointerEvents: 'none' }}>
                      {n.label.replace(' (Synthetic)', '').slice(0, 22)}
                    </text>
                  </g>
                )
              })}
            </g>
          </svg>
        </Card>

        <div className="stack gap12">
          {/* Top Hubs Card */}
          <Card title="Key Hubs & Centrality">
            <div className="stack gap4">
              {topHubs.map((h) => (
                <div key={h.id} className="row between gap6" style={{ padding: '3px 0', borderBottom: '1px solid var(--line)' }}>
                  <span className="tiny" style={{ cursor: 'pointer' }} onClick={() => inspect(h)}>
                    {h.label.slice(0, 22)}
                  </span>
                  <Badge tone="blue">{nodeDegrees[h.id] ?? 0} links</Badge>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Legend">
            <div className="eyebrow" style={{ marginBottom: 6 }}>Edge provenance</div>
            {Object.entries(PROV_COLOR).map(([k, c]) => (
              <div className="legend-row" key={k}>
                <span className="legend-swatch" style={{ background: c }} />
                <span className="tiny">{k}</span>
                <span className="tiny muted" style={{ marginLeft: 'auto' }}>
                  {(data?.edges ?? []).filter((e) => e.provenance === k).length}
                </span>
              </div>
            ))}
            <div className="hr" />
            <div className="eyebrow" style={{ marginBottom: 6 }}>Node type</div>
            {Object.entries(TYPE_COLOR).filter(([t]) => types.includes(t)).map(([k, c]) => (
              <div className="legend-row" key={k}>
                <span className="legend-swatch" style={{ background: c, borderRadius: '50%' }} />
                <span className="tiny">{k.replace(/_/g, ' ')}</span>
              </div>
            ))}
          </Card>

          <Card title="Selected entity">
            {!selected ? <Empty>Click any node to inspect evidence or set path</Empty> : (
              <div className="stack gap6">
                <div style={{ fontSize: 12.5, fontWeight: 600 }}>{selected.label}</div>
                <div className="row gap6">
                  <Badge tone="neutral">{selected.type}</Badge>
                  <Badge>{selected.status}</Badge>
                  <Badge tone="blue">{nodeDegrees[selected.id] ?? 0} connections</Badge>
                </div>
                <dl className="kv">
                  <dt>District</dt><dd>{selected.district || '—'}</dd>
                  <dt>Confidence</dt><dd>{(selected.confidence * 100).toFixed(0)}%</dd>
                </dl>
                <div className="row gap4" style={{ marginTop: 4 }}>
                  <button className="btn sm" onClick={() => inspect(selected)}>Evidence panel</button>
                  {pathMode && (
                    <button className="btn sm primary" onClick={() => {
                      if (!sourceId) setSourceId(selected.id)
                      else setTargetId(selected.id)
                    }}>
                      {!sourceId ? 'Set Source' : 'Set Target'}
                    </button>
                  )}
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>
    </Section>
  )
}
