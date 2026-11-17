import { useState, useMemo } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api, type EntityRow } from '../api'
import { Card, Empty, Section, Spinner, SyntheticBanner, Badge } from '../components/ui'
import { IcGraph, IcMap } from '../components/icons'
import GeoPage from './GeoPage'
import GraphPage from './GraphPage'

export default function ExplorePage() {
  const [params, setParams] = useSearchParams()
  const activeTab = (params.get('tab') as 'map' | 'connections' | 'records' | 'timeline') || 'map'
  const nav = useNavigate()

  // Records view query
  const [recordQuery, setRecordQuery] = useState('')
  const entities = useQuery({
    queryKey: ['explore-records'],
    queryFn: () => api.get<EntityRow[]>('/entities?limit=250'),
    enabled: activeTab === 'records',
  })

  const filteredRecords = useMemo(() => {
    const list = entities.data ?? []
    if (!recordQuery.trim()) return list
    const q = recordQuery.toLowerCase()
    return list.filter(
      (e) =>
        e.name.toLowerCase().includes(q) ||
        e.district.toLowerCase().includes(q) ||
        e.entity_type.toLowerCase().includes(q)
    )
  }, [entities.data, recordQuery])

  return (
    <div>
      <div className="tabs" style={{ marginBottom: 12 }}>
        <button
          className={`tab${activeTab === 'map' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'map' })}
        >
          <IcMap size={14} style={{ display: 'inline', marginRight: 5, verticalAlign: 'middle' }} />
          Geospatial Map
        </button>
        <button
          className={`tab${activeTab === 'connections' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'connections' })}
        >
          <IcGraph size={14} style={{ display: 'inline', marginRight: 5, verticalAlign: 'middle' }} />
          Connections (Knowledge Graph)
        </button>
        <button
          className={`tab${activeTab === 'records' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'records' })}
        >
          Exploration Records
        </button>
        <button
          className={`tab${activeTab === 'timeline' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'connections', timeline: 'true' })}
        >
          Timeline Scrubber
        </button>
      </div>

      {activeTab === 'map' && <GeoPage />}
      {activeTab === 'connections' && <GraphPage />}
      {activeTab === 'records' && (
        <Section
          title="Exploration Records"
          sub="Canonical record registry with direct links to geographical visualization and connection analysis."
        >
          <SyntheticBanner />
          <div className="toolbar" style={{ marginBottom: 12 }}>
            <div className="searchbox" style={{ maxWidth: 450 }}>
              <input
                className="input"
                placeholder="Search entities by name, type or district…"
                value={recordQuery}
                onChange={(e) => setRecordQuery(e.target.value)}
              />
            </div>
          </div>

          <Card title={`Monitored Installation Records (${filteredRecords.length})`} bodyStyle={{ padding: 0 }}>
            {entities.isLoading ? (
              <Spinner label="Loading records for exploration…" />
            ) : filteredRecords.length === 0 ? (
              <Empty>No records found matching your query.</Empty>
            ) : (
              <div className="tbl-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Type</th>
                      <th>District / Sector</th>
                      <th>Status</th>
                      <th>Coordinates</th>
                      <th>Exploration Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRecords.map((r) => (
                      <tr key={r.id}>
                        <td style={{ fontWeight: 500 }}>{r.name}</td>
                        <td><Badge tone="neutral">{r.entity_type}</Badge></td>
                        <td>{r.district || '—'}</td>
                        <td><Badge tone={r.status}>{r.status}</Badge></td>
                        <td className="tiny mono">{r.latitude || '—'}, {r.longitude || '—'}</td>
                        <td>
                          <div className="row gap6">
                            <button
                              className="btn sm ghost"
                              onClick={() => nav(`/explore?tab=map&entityId=${r.id}`)}
                            >
                              View on Map
                            </button>
                            <button
                              className="btn sm ghost"
                              onClick={() => nav(`/explore?tab=connections&node=${r.id}`)}
                            >
                              View Graph
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </Section>
      )}
    </div>
  )
}
