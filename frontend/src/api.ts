import { useAuth } from './store'

const BASE = '/api/v1'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = useAuth.getState().token
  const headers: Record<string, string> = { ...(init.headers as Record<string, string>) }
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (init.body && !(init.body instanceof FormData)) headers['Content-Type'] = 'application/json'
  const res = await fetch(`${BASE}${path}`, { ...init, headers })
  if (res.status === 401 && token) {
    useAuth.getState().clear()
  }
  if (!res.ok) {
    let msg = `Request failed (${res.status})`
    try {
      const j = await res.json()
      msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail ?? j)
    } catch { /* non-JSON error body */ }
    throw new ApiError(msg, res.status)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  get: <T,>(p: string) => request<T>(p),
  post: <T,>(p: string, body?: unknown) =>
    request<T>(p, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) }),
  patch: <T,>(p: string, body?: unknown) =>
    request<T>(p, { method: 'PATCH', body: body === undefined ? undefined : JSON.stringify(body) }),
  upload: <T,>(p: string, form: FormData) => request<T>(p, { method: 'POST', body: form }),
}

export type Overview = {
  entities: number; relationships: number; datasets: number; documents: number
  cases: number; open_cases: number
  entities_by_type: Record<string, number>
  entities_by_status: Record<string, number>
  relationships_by_provenance: Record<string, number>
  data_basis: string
}

export type EntityRow = {
  id: string; organization_id: string; entity_type: string; name: string
  description: string; district: string; state: string; status: string
  confidence: number; is_synthetic: boolean
  classification?: string
  latitude?: number
  longitude?: number
}

export type Citation = {
  id: string; kind: string; record_id: string; title: string
  classification: string; synthetic: boolean; snippet: string; score: number
}

export type AIResult = {
  answer: string; citations: Citation[]; confidence: number
  insufficient_evidence: boolean
  meta: { prompt_version: string; provider: string; retrieved: number; model_invoked: boolean }
  conversation_id?: string
}

export type SearchHit = {
  kind: string; id: string; title: string; snippet: string
  classification: string; synthetic: boolean; score: number
}

export type ImpactEdge = {
  id: string
  source_id: string
  target_id: string
  source_name: string
  target_name: string
  rel_type: string
  provenance: string
  confidence: number
  evidence: string
  source_ref: string
  is_hypothesis: boolean
}

export type ImpactNode = {
  id: string
  name: string
  entity_type: string
  district: string
  state: string
  status: string
  confidence: number
  classification: string
  attributes?: Record<string, any>
  hop_distance: number
  path: ImpactEdge[]
  path_confidence: number
  is_hypothesis: boolean
}

export type ImpactResponse = {
  root_entity: {
    id: string
    name: string
    entity_type: string
    district: string
    state: string
    status: string
    confidence: number
    classification: string
    attributes?: Record<string, any>
  }
  depth: number
  direction: 'downstream' | 'upstream' | 'both'
  total_affected: number
  nodes: ImpactNode[]
  edges: ImpactEdge[]
}

export const ROLES = ['platform_admin', 'org_admin', 'data_admin', 'analyst', 'reviewer', 'readonly', 'auditor']

export const roleLabel = (r: string) => r.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

export const fmtDate = (s?: string | null) =>
  s ? new Date(s).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false }) : '—'

export const fmtDateShort = (s?: string | null) =>
  s ? new Date(s).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric' }) : '—'

export const inr = (n: number) => new Intl.NumberFormat('en-IN').format(n)
