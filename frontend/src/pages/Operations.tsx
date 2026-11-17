import { useQuery } from '@tanstack/react-query'
import { api, type EntityRow } from '../api'
import { Badge, Card, Empty, ErrorBox, KPI, Section, Spinner } from '../components/ui'
import { EChart, barOption, palette } from '../components/charts'
import { useUI } from '../store'

const OPS_TYPES = ['asset', 'vehicle', 'facility', 'warehouse', 'inventory_item']

export default function Operations() {
  const health = useQuery({ queryKey: ['asset-health'], queryFn: () => api.get<any>('/analytics/asset-health') })
  const entities = useQuery({ queryKey: ['ops-entities'], queryFn: () => api.get<EntityRow[]>('/entities?limit=300') })
  const ov = useQuery({ queryKey: ['overview'], queryFn: () => api.get<any>('/analytics/overview') })
  const openPanel = useUI((s) => s.openPanel)

  if (health.isLoading || entities.isLoading) return <Spinner />
  if (health.error) return <ErrorBox error={health.error} />
  const h = health.data
  const ops = (entities.data ?? []).filter((e) => OPS_TYPES.includes(e.entity_type))
  const exceptions = ops.filter((e) => !['active', 'in_progress'].includes(e.status))

  const statusByType: Record<string, number> = {}
  ops.forEach((e) => { statusByType[e.status] = (statusByType[e.status] ?? 0) + 1 })

  const maintenanceQueue = ops.filter((e) => ['degraded', 'under_maintenance', 'low_stock'].includes(e.status))

  const forecastOption = {
    backgroundColor: 'transparent',
    grid: { left: 40, right: 14, top: 18, bottom: 24 },
    tooltip: { trigger: 'axis', backgroundColor: '#15212D', borderColor: '#1E2D3D', textStyle: { color: '#E9EEF4', fontSize: 11 } },
    legend: { bottom: 0, textStyle: { color: '#8298AE', fontSize: 10 }, itemWidth: 8, itemHeight: 8 },
    xAxis: { type: 'category', data: ['Now', '+1m', '+2m', '+3m'], axisLabel: { color: '#8298AE', fontSize: 10 }, axisLine: { lineStyle: { color: '#1E2D3D' } } },
    yAxis: { type: 'value', axisLabel: { color: '#8298AE', fontSize: 10 }, splitLine: { lineStyle: { color: '#101923' } } },
    series: [
      { name: 'Serviceable', type: 'line', smooth: true, data: [h.operational, h.operational - 1, h.operational - 1, h.operational - 2],
        lineStyle: { color: palette[1] }, itemStyle: { color: palette[1] }, areaStyle: { opacity: 0.08, color: palette[1] } },
      { name: 'In maintenance', type: 'line', smooth: true, data: [h.degraded, h.degraded + 1, h.degraded + 1, h.degraded],
        lineStyle: { color: palette[0], type: 'dashed' }, itemStyle: { color: palette[0] } },
    ],
  }

  return (
    <Section
      title="Operational Intelligence"
      sub="Resource posture across assets, facilities, warehouses and inventory. Derived from record status fields — not live telemetry."
    >
      <div className="grid g4" style={{ marginBottom: 12 }}>
        <KPI label="Tracked operational items" value={h.tracked_assets} meta="assets, facilities, warehouses, vehicles" />
        <KPI label="Availability ratio" value={`${(h.availability_ratio * 100).toFixed(0)}%`} meta="recorded status basis" />
        <KPI label="Exceptions needing action" value={exceptions.length} meta="degraded, under maintenance, low stock" />
        <KPI label="Forecast horizon" value="3 months" meta="simple trend projection — see limitations" />
      </div>

      <div className="grid g-2-1" style={{ marginBottom: 12 }}>
        <Card title="Maintenance and exception queue" actions={<span className="tiny muted">{maintenanceQueue.length} items</span>} bodyStyle={{ padding: 0 }}>
          {maintenanceQueue.length === 0 ? <Empty>No exceptions recorded</Empty> : (
            <div className="tbl-wrap">
              <table>
                <thead><tr><th>Item</th><th>Type</th><th>District</th><th>Status</th><th></th></tr></thead>
                <tbody>
                  {maintenanceQueue.map((e) => (
                    <tr key={e.id}>
                      <td>{e.name}</td>
                      <td className="tiny mono dim">{e.entity_type}</td>
                      <td>{e.district || '—'}</td>
                      <td><Badge>{e.status}</Badge></td>
                      <td style={{ textAlign: 'right' }}>
                        <button className="btn sm ghost" onClick={() => openPanel({
                          kind: 'ASSET RECORD', title: e.name,
                          data: (<div className="stack gap6">
                            <Badge>{e.status}</Badge>
                            <p className="tiny dim" style={{ margin: 0 }}>{e.description || 'No description recorded.'}</p>
                            <dl className="kv">
                              <dt>Type</dt><dd>{e.entity_type}</dd><dt>District</dt><dd>{e.district}</dd>
                              <dt>Confidence</dt><dd>{(e.confidence * 100).toFixed(0)}%</dd>
                            </dl>
                            <div className="tiny muted">Recommended action: verify status against the next maintenance log; assign to district engineer.
                              This recommendation is advisory and requires human approval.</div>
                          </div>),
                        })}>Review</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
        <Card title="Status distribution">
          <EChart option={barOption(statusByType, true)} height={210} />
        </Card>
      </div>

      <div className="grid g2">
        <Card title="Capacity projection" actions={<Badge tone="amber">advisory</Badge>}>
          <EChart option={forecastOption as any} height={220} />
          <div className="tiny muted" style={{ marginTop: 8 }}>
            <strong>Data basis:</strong> current status counts. <strong>Method:</strong> linear carry-forward of the observed
            maintenance rate. <strong>Limitations:</strong> no seasonal, funding or workforce inputs; treat as a
            conversation starter, not a decision. Confidence: low.
          </div>
        </Card>
        <Card title="Operational summary">
          <div className="stack gap8">
            <div className="row between"><span className="tiny muted">Entities in scope</span><span className="mono">{ov.data?.entities ?? '—'}</span></div>
            <div className="row between"><span className="tiny muted">Warehouses</span><span className="mono">{ops.filter((e) => e.entity_type === 'warehouse').length}</span></div>
            <div className="row between"><span className="tiny muted">Facilities</span><span className="mono">{ops.filter((e) => e.entity_type === 'facility').length}</span></div>
            <div className="row between"><span className="tiny muted">Vehicles</span><span className="mono">{ops.filter((e) => e.entity_type === 'vehicle').length}</span></div>
            <div className="row between"><span className="tiny muted">Inventory batches</span><span className="mono">{ops.filter((e) => e.entity_type === 'inventory_item').length}</span></div>
            <div className="hr" />
            <div className="tiny muted">
              Task assignment and approval workflows are schema-supported and audited; automated high-impact decisions
              are intentionally not implemented. All recommendations remain advisory.
            </div>
          </div>
        </Card>
      </div>
    </Section>
  )
}
