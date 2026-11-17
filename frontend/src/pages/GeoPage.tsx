import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { api } from '../api'
import { Badge, Card, Section, Spinner } from '../components/ui'
import { useUI } from '../store'

const ODISHA_CENTER: [number, number] = [85.2, 20.4]

// Offline-capable style: no external tile or glyph requests. Layers are drawn from platform GeoJSON.
const BASE_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  name: 'VEGA Tactical Command Reference',
  sources: {},
  layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#0B1118' } }],
}

function createGeoCircle(center: [number, number], radiusKm: number) {
  const points = 64
  const coords: [number, number][] = []
  const distanceX = radiusKm / (111.32 * Math.cos((center[1] * Math.PI) / 180))
  const distanceY = radiusKm / 110.574
  for (let i = 0; i < points; i++) {
    const theta = (i / points) * (2 * Math.PI)
    const x = distanceX * Math.cos(theta)
    const y = distanceY * Math.sin(theta)
    coords.push([center[0] + x, center[1] + y])
  }
  coords.push(coords[0])
  return {
    type: 'Feature' as const,
    geometry: { type: 'Polygon' as const, coordinates: [coords] },
    properties: { radiusKm },
  }
}

function haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number) {
  const R = 6371
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

export default function GeoPage() {
  const mapEl = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const popupRef = useRef<maplibregl.Popup | null>(null)
  const { openPanel } = useUI()
  const [ready, setReady] = useState(false)
  const [layers, setLayers] = useState({ assets: true, facilities: true, heat: false, districts: true, alerts: false })
  const [q, setQ] = useState('')
  const [selected, setSelected] = useState<any>(null)
  const [bufferKm, setBufferKm] = useState<number | null>(null)

  const assets = useQuery({ queryKey: ['geo-assets'], queryFn: () => api.get<any>('/geo/assets') })
  const districts = useQuery({ queryKey: ['geo-districts'], queryFn: () => api.get<any>('/geo/districts') })
  const summary = useQuery({ queryKey: ['geo-summary'], queryFn: () => api.get<any>('/geo/summary') })

  useEffect(() => {
    if (!mapEl.current || mapRef.current) return
    const map = new maplibregl.Map({
      container: mapEl.current,
      style: BASE_STYLE,
      center: ODISHA_CENTER,
      zoom: 6.9,
      attributionControl: false,
      dragRotate: false,
    })
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    map.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-right')
    map.on('load', () => setReady(true))
    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, [])

  // install sources + layers once data arrives
  useEffect(() => {
    const map = mapRef.current
    if (!map || !ready || !assets.data || !districts.data) return

    const feats = (assets.data.features ?? []).map((f: any) => {
      const lat = f.geometry.coordinates[1], lon = f.geometry.coordinates[0]
      const district = (summary.data?.districts ?? []).find((d: any) => d.district === f.properties.district)
      return { ...f, properties: { ...f.properties, district_count: district?.count ?? 1, lat, lon } }
    })
    const geo = { type: 'FeatureCollection' as const, features: feats }
    const distGeo = {
      type: 'FeatureCollection' as const,
      features: (districts.data.features ?? []).map((f: any) => {
        const s = (summary.data?.districts ?? []).find((d: any) => d.district === f.properties.district)
        return { ...f, properties: { ...f.properties, count: s?.count ?? 0 } }
      }),
    }

    if (map.getSource('assets')) {
      (map.getSource('assets') as maplibregl.GeoJSONSource).setData(geo as any)
      ;(map.getSource('districts') as maplibregl.GeoJSONSource).setData(distGeo as any)
      return
    }

    map.addSource('districts', { type: 'geojson', data: distGeo as any })
    map.addSource('assets', { type: 'geojson', data: geo as any, cluster: true, clusterRadius: 44, clusterMaxZoom: 5 })

    map.addLayer({
      id: 'district-halo', type: 'circle', source: 'districts',
      paint: {
        'circle-radius': ['interpolate', ['linear'], ['get', 'count'], 0, 9, 8, 26],
        'circle-color': '#d9a13b', 'circle-opacity': 0.035,
        'circle-stroke-color': '#d9a13b', 'circle-stroke-opacity': 0.12, 'circle-stroke-width': 0.6,
      },
    })
    map.addLayer({
      id: 'heat', type: 'heatmap', source: 'assets', maxzoom: 11, layout: { visibility: 'none' },
      paint: {
        'heatmap-weight': 1, 'heatmap-intensity': 0.9,
        'heatmap-color': ['interpolate', ['linear'], ['heatmap-density'],
          0, 'rgba(0,0,0,0)', 0.3, 'rgba(95,179,161,0.35)', 0.6, 'rgba(217,161,59,0.55)', 1, 'rgba(217,83,79,0.75)'],
        'heatmap-radius': 34, 'heatmap-opacity': 0.72,
      },
    })
    map.addLayer({
      id: 'clusters', type: 'circle', source: 'assets', filter: ['has', 'point_count'],
      paint: {
        'circle-color': '#ffffff', 'circle-stroke-color': '#b45309', 'circle-stroke-width': 1.8,
        'circle-radius': ['step', ['get', 'point_count'], 15, 3, 20, 6, 25],
        'circle-opacity': 0.95,
      },
    })
    map.addLayer({
      id: 'assets', type: 'circle', source: 'assets', filter: ['!', ['has', 'point_count']],
      paint: {
        'circle-radius': ['match', ['get', 'entity_type'], 'warehouse', 8, 'facility', 7.5, 'vehicle', 6.5, 7],
        'circle-color': ['match', ['get', 'entity_type'],
          'warehouse', '#2563eb', 'facility', '#7c3aed', 'vehicle', '#16a34a', 'inventory_item', '#64748b', '#0d9488'],
        'circle-stroke-color': '#ffffff', 'circle-stroke-width': 1.5, 'circle-stroke-opacity': 0.85, 'circle-opacity': 0.95,
      },
    })
    map.addLayer({
      id: 'asset-labels', type: 'circle', source: 'assets', filter: ['!', ['has', 'point_count']],
      paint: { 'circle-radius': 13, 'circle-color': '#ffffff', 'circle-opacity': 0.001 },
    })

    // Frame the authorized record extent once, rather than relying on a hardcoded centre.
    const coords = feats.map((f: any) => f.geometry.coordinates as [number, number])
    if (coords.length > 1) {
      const lons = coords.map((c: [number, number]) => c[0]), lats = coords.map((c: [number, number]) => c[1])
      map.fitBounds(
        [[Math.min(...lons) - 0.25, Math.min(...lats) - 0.25], [Math.max(...lons) + 0.25, Math.max(...lats) + 0.25]],
        { padding: { top: 40, bottom: 60, left: 70, right: 40 }, duration: 0, maxZoom: 8.4 },
      )
    }

    map.on('click', 'assets', (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
      const f = e.features?.[0]
      if (!f) return
      const p: any = f.properties
      setSelected(p)
      popupRef.current?.remove()
      popupRef.current = new maplibregl.Popup({ closeButton: true, className: 'vega-popup' })
        .setLngLat((f.geometry as any).coordinates)
        .setHTML(`<div style="font:12px/1.45 -apple-system,sans-serif;color:#E9EEF4;background:#15212D;padding:10px 12px;border:1px solid #1E2D3D;box-shadow:0 8px 24px rgba(0,0,0,0.6);border-radius:4px;min-width:180px">
          <div style="font-weight:600;color:#D5A13C;font-size:12.5px">${p.name}</div>
          <div style="color:#8298AE;margin-top:2px">${p.entity_type} · ${p.district}</div>
          <div style="color:#CBD5E1;margin-top:2px">Status: ${p.status} · Confidence: ${(p.confidence * 100).toFixed(0)}%</div>
          <div style="color:#55687A;margin-top:5px;font-size:10px;letter-spacing:0.04em">SOVEREIGN DEFENCE RECORD</div></div>`)
        .addTo(map)
    })
    map.on('click', 'clusters', (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
      const f = e.features?.[0]
      if (!f) return
      const src = map.getSource('assets') as maplibregl.GeoJSONSource
      void src.getClusterExpansionZoom((f.properties as any).cluster_id).then(
        (zoom: number) => map.easeTo({ center: (f.geometry as any).coordinates, zoom: zoom ?? map.getZoom() + 1 }),
        () => { /* cluster may already be resolved; ignore */ },
      )
    })
    map.on('mouseenter', 'assets', () => { map.getCanvas().style.cursor = 'pointer' })
    map.on('mouseleave', 'assets', () => { map.getCanvas().style.cursor = '' })
  }, [ready, assets.data, districts.data, summary.data])

  // layer visibility + text filter
  useEffect(() => {
    const map = mapRef.current
    if (!map || !ready) return
    const set = (id: string, v: boolean) => { if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', v ? 'visible' : 'none') }
    set('assets', layers.assets && !q.trim())
    set('clusters', layers.assets && !q.trim())
    set('asset-labels', false)
    set('heat', layers.heat)
    set('district-halo', layers.districts)
    set('assets', (layers.assets || layers.facilities) && !q.trim())

    const filtered = q.trim()
    if (map.getLayer('assets') && filtered) {
      map.setFilter('assets', ['all', ['!', ['has', 'point_count']], ['in', filtered.toLowerCase(), ['downcase', ['get', 'name']]]])
      map.setLayoutProperty('assets', 'visibility', 'visible')
      map.setLayoutProperty('clusters', 'visibility', 'none')
    } else if (map.getLayer('assets')) {
      map.setFilter('assets', ['!', ['has', 'point_count']])
    }
  }, [layers, q, ready])

  // tactical buffer zone layer
  useEffect(() => {
    const map = mapRef.current
    if (!map || !ready) return
    const empty = { type: 'FeatureCollection' as const, features: [] }
    if (!bufferKm || !selected?.lat || !selected?.lon) {
      if (map.getSource('buffer')) {
        ;(map.getSource('buffer') as maplibregl.GeoJSONSource).setData(empty as any)
      }
      return
    }
    const circle = createGeoCircle([selected.lon, selected.lat], bufferKm)
    const fc = { type: 'FeatureCollection' as const, features: [circle] }
    if (map.getSource('buffer')) {
      ;(map.getSource('buffer') as maplibregl.GeoJSONSource).setData(fc as any)
    } else {
      map.addSource('buffer', { type: 'geojson', data: fc as any })
      map.addLayer({
        id: 'buffer-fill', type: 'fill', source: 'buffer',
        paint: { 'fill-color': '#b45309', 'fill-opacity': 0.14 },
      }, 'clusters')
      map.addLayer({
        id: 'buffer-line', type: 'line', source: 'buffer',
        paint: { 'line-color': '#b45309', 'line-width': 1.8, 'line-dasharray': [4, 2] },
      }, 'clusters')
    }
  }, [bufferKm, selected, ready])

  const nearbyCount = useMemo(() => {
    if (!bufferKm || !selected?.lat || !selected?.lon || !assets.data?.features) return 0
    return (assets.data.features as any[]).filter((f) => {
      const [lon, lat] = f.geometry.coordinates
      const d = haversineDistance(selected.lat, selected.lon, lat, lon)
      return d <= bufferKm
    }).length
  }, [bufferKm, selected, assets.data])

  const counts = summary.data?.districts ?? []
  const maxCount = Math.max(1, ...counts.map((c: any) => c.count))

  return (
    <Section
      title="Geospatial Explorer"
      sub="District-anchored view of authorized assets and facilities. Positions are approximations derived from administrative geography, not survey-grade coordinates."
      actions={
        <div className="row gap6">
          <input className="input" style={{ width: 190 }} placeholder="Filter assets on map…" value={q} onChange={(e) => setQ(e.target.value)} />
          <span className="badge neutral">{(assets.data?.features ?? []).length} features</span>
        </div>
      }
    >
      <div className="grid g-2-1">
        <div className="map-shell">
          <div ref={mapEl} className="map-el" />
          {!ready && <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', background: 'var(--bg)' }}><Spinner label="Initialising tactical map engine…" /></div>}
          <div className="map-legend">
            <div className="eyebrow" style={{ marginBottom: 5 }}>Layers</div>
            {([
              ['assets', 'Assets'],
              ['facilities', 'Facilities'],
              ['heat', 'Density heatmap'],
              ['districts', 'District anchors'],
              ['alerts', 'Tactical threat alerts (none)'],
            ] as const).map(([k, label]) => (
              <label key={k} className="legend-row" style={{ cursor: 'pointer' }}>
                <input type="checkbox" checked={(layers as any)[k]} disabled={k === 'alerts'}
                  onChange={(e) => setLayers((s) => ({ ...s, [k]: e.target.checked }))} />
                <span className="tiny">{label}</span>
              </label>
            ))}
            <div className="hr" style={{ margin: '7px 0' }} />
            <div className="legend-row"><span className="legend-swatch" style={{ background: '#5FB3A1' }} /><span className="tiny">asset</span></div>
            <div className="legend-row"><span className="legend-swatch" style={{ background: '#6D8CFF' }} /><span className="tiny">warehouse</span></div>
            <div className="legend-row"><span className="legend-swatch" style={{ background: '#A78BFA' }} /><span className="tiny">facility</span></div>
            <div className="legend-row"><span className="legend-swatch" style={{ background: '#5AA87A' }} /><span className="tiny">vehicle</span></div>
          </div>
          <div style={{ position: 'absolute', bottom: 34, right: 10, fontSize: 10, color: 'var(--text-3)', textAlign: 'right', background: 'rgba(16,25,35,0.85)', border: '1px solid var(--line)', padding: '4px 8px', borderRadius: 3, backdropFilter: 'blur(4px)' }}>
            Reference geometry: public administrative geography<br />
            Data freshness: {new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} IST
          </div>
        </div>

        <div className="stack gap12">
          <Card title="Region summary" actions={<Badge tone="neutral">live</Badge>}>
            {summary.isLoading ? <Spinner /> : (
              <div className="stack gap4">
                {counts.slice(0, 8).map((d: any) => (
                  <div key={d.district}>
                    <div className="row between">
                      <span className="tiny">{d.district}</span>
                      <span className="tiny mono muted">{d.count}</span>
                    </div>
                    <div style={{ height: 3, background: 'var(--line)', marginTop: 3, borderRadius: 2 }}>
                      <div style={{ height: 3, width: `${(d.count / maxCount) * 100}%`, background: 'var(--accent)', borderRadius: 2 }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="tiny muted" style={{ marginTop: 8 }}>
              Counts cover your organization's records only.
            </div>
          </Card>

          <Card title="Selected feature">
            {!selected ? <div className="empty">Click a map feature to inspect it</div> : (
              <div className="stack gap6">
                <div style={{ fontSize: 12.5 }}>{selected.name}</div>
                <div className="row gap6"><Badge tone="neutral">{selected.entity_type}</Badge><Badge>{selected.status}</Badge></div>
                <dl className="kv">
                  <dt>District</dt><dd>{selected.district}</dd>
                  <dt>Coordinates</dt><dd className="mono tiny">{Number(selected.lon).toFixed(4)}, {Number(selected.lat).toFixed(4)}</dd>
                  <dt>Confidence</dt><dd>{(selected.confidence * 100).toFixed(0)}%</dd>
                </dl>
                <div style={{ marginTop: 6, padding: '8px 0', borderTop: '1px solid var(--line)' }}>
                  <div className="eyebrow" style={{ marginBottom: 4 }}>Tactical Radius Buffer</div>
                  <div className="row gap4">
                    {[25, 50, 100].map((km) => (
                      <button key={km} className={`btn sm ${bufferKm === km ? 'primary' : ''}`}
                        onClick={() => setBufferKm(bufferKm === km ? null : km)}>
                        {km} km
                      </button>
                    ))}
                    {bufferKm && <button className="btn sm ghost" onClick={() => setBufferKm(null)}>Clear</button>}
                  </div>
                  {bufferKm && (
                    <div className="tiny" style={{ marginTop: 5, color: 'var(--accent)', fontWeight: 600 }}>
                      🎯 {nearbyCount} assets within {bufferKm} km radius
                    </div>
                  )}
                </div>
                <button className="btn sm" onClick={() => openPanel({
                  kind: 'GEOSPATIAL RECORD', title: selected.name,
                  data: <div className="tiny muted">Entity {selected.name} located in {selected.district}. Position is a district-anchored approximation. Full record available in the Data Catalog.</div>,
                })}>Open in side panel</button>
              </div>
            )}
          </Card>

          <Card title="Boundary data status">
            <div className="banner warn">
              District boundaries are represented by reference anchors in this build. Production deployment requires
              licensed Survey of India / Census administrative geometry loaded into PostGIS.
            </div>
          </Card>
        </div>
      </div>
    </Section>
  )
}
