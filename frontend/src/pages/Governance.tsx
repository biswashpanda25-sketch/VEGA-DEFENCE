import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, fmtDate } from '../api'
import { useAuth } from '../store'
import { Badge, Card, KPI, Section, Spinner } from '../components/ui'

type Chain = { valid: boolean; checked: number; head?: string; tail?: string; broken_at?: string; reason?: string }
type ClearanceUser = { id: string; email: string; full_name: string; role: string; clearance: string; mfa_enabled: boolean }
type ClearanceList = { levels: string[]; users: ClearanceUser[] }
type Job = {
  id: string; status: string; attempts: number; max_attempts: number; kind: string
  last_error?: string | null; dataset_id?: string | null; next_attempt_at?: string | null; created_at: string
}

const TONE: Record<string, string> = { PROTECTED: 'danger', RESTRICTED: 'warn', INTERNAL: 'ok' }

/**
 * Governance console: the operational surface for the controls that are otherwise only API-visible —
 * audit-chain integrity, data clearances, MFA enrolment and the connector job ledger. Every panel reads
 * live state and reports the permission refusal explicitly instead of hiding the control.
 */
export default function Governance() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [secret, setSecret] = useState<{ secret: string; otpauth_uri: string } | null>(null)
  const [code, setCode] = useState('')
  const [notice, setNotice] = useState<string>('')

  const chain = useQuery<Chain>({ queryKey: ['audit-verify'], queryFn: () => api.get<Chain>('/audit/verify'), retry: 0 })
  const clearances = useQuery<ClearanceList>({
    queryKey: ['clearances'], queryFn: () => api.get<ClearanceList>('/admin/clearances'), retry: 0,
  })
  const jobs = useQuery<Job[]>({ queryKey: ['jobs'], queryFn: () => api.get<Job[]>('/admin/jobs'), retry: 0 })

  const verify = useMutation({
    mutationFn: () => api.get<Chain>('/audit/verify'),
    onSuccess: (d) => { qc.setQueryData(['audit-verify'], d); setNotice(d.valid ? 'Chain verified' : 'Chain integrity failure') },
  })

  const setClearance = useMutation({
    mutationFn: ({ id, level }: { id: string; level: string }) =>
      api.patch<any>(`/admin/users/${id}/clearance?clearance=${level}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['clearances'] }); setNotice('Clearance updated and audited') },
    onError: (e) => setNotice(`Refused: ${(e as Error).message}`),
  })

  const enroll = useMutation({
    mutationFn: () => api.post<{ secret: string; otpauth_uri: string }>('/auth/mfa/enroll'),
    onSuccess: (d) => { setSecret(d); setNotice('Scan the URI in your authenticator, then enter the 6-digit code') },
  })

  const activate = useMutation({
    mutationFn: (c: string) => api.post<any>(`/auth/mfa/activate?code=${encodeURIComponent(c)}`),
    onSuccess: () => { setNotice('MFA activated for this account'); setSecret(null); setCode('') },
    onError: (e) => setNotice(`Code rejected: ${(e as Error).message}`),
  })

  return (
    <Section
      title="Governance"
      sub="Audit integrity, data clearances, multi-factor enrolment and the connector job ledger — the controls behind every other screen."
    >
      {notice && <div className="banner">{notice}</div>}

      <div className="grid g3">
        <KPI label="Audit chain" value={chain.data ? (chain.data.valid ? 'Verified' : 'Broken') : '…'}
             meta={chain.data ? `${chain.data.checked} rows checked` : undefined} />
        <KPI label="Your clearance" value={user?.clearance ?? 'INTERNAL'}
             meta={user ? `role ${user.role}` : undefined} />
        <KPI label="Connector jobs" value={jobs.data?.length ?? '…'}
             meta={jobs.data ? `${jobs.data.filter((j) => j.status === 'dead_letter').length} in dead-letter` : undefined} />
      </div>

      <Card title="Audit chain integrity"
            actions={<button className="btn" onClick={() => verify.mutate()} disabled={verify.isPending}>
              {verify.isPending ? 'Verifying…' : 'Verify now'}
            </button>}>
        {chain.error && (
          <div className="banner warn">
            Chain verification requires auditor, organization administrator or platform administrator privileges.
            Your current role does not include it, and this refusal is itself recorded in the audit log.
          </div>
        )}
        {chain.isLoading && <Spinner />}
        {chain.data && (
          <div className="stack">
            <div className="row">
              <Badge tone={chain.data.valid ? 'ok' : 'danger'}>{chain.data.valid ? 'chain valid' : 'tampering detected'}</Badge>
              <span className="muted">{chain.data.checked} rows in the hash chain</span>
            </div>
            {chain.data.head && <div className="mono small">head {chain.data.head}</div>}
            {chain.data.tail && <div className="mono small">tail {chain.data.tail}</div>}
            {!chain.data.valid && (
              <div className="banner warn">
                Row {chain.data.broken_at ?? 'unknown'} failed verification: {chain.data.reason ?? 'hash mismatch'}.
              </div>
            )}
            <p className="muted small">
              Each audit row hashes its own fields together with the previous row's hash. Recomputing the chain
              detects edits, deletions and reordering. A database superuser can still delete the whole chain —
              append-only export to WORM storage is tracked as a known gap.
            </p>
          </div>
        )}
      </Card>

      <Card title="Data clearances">
        <p className="muted small">Clearance is enforced on every read path, including search and AI retrieval.</p>
        {clearances.error && (
          <div className="banner warn">
            Clearance administration requires platform administrator privileges. Refusal is recorded in the audit log.
          </div>
        )}
        {clearances.isLoading && <Spinner />}
        {clearances.data && (
          <table className="table">
            <thead>
              <tr><th>User</th><th>Role</th><th>Clearance</th><th>MFA</th><th>Set clearance</th></tr>
            </thead>
            <tbody>
              {clearances.data.users.map((u) => (
                <tr key={u.id}>
                  <td>{u.full_name}<div className="muted small">{u.email}</div></td>
                  <td>{u.role}</td>
                  <td><Badge tone={TONE[u.clearance] ?? 'ok'}>{u.clearance}</Badge></td>
                  <td>{u.mfa_enabled ? <Badge tone="ok">enrolled</Badge> : <span className="muted">—</span>}</td>
                  <td>
                    <select defaultValue="" onChange={(e) => e.target.value && setClearance.mutate({ id: u.id, level: e.target.value })}>
                      <option value="">change…</option>
                      {clearances.data.levels.map((l) => <option key={l} value={l}>{l}</option>)}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Card title="Multi-factor authentication">
        <p className="muted small">TOTP. Once active, sign-in requires the current 6-digit code.</p>
        {user?.mfa_enabled ? (
          <div className="row"><Badge tone="ok">MFA active</Badge><span className="muted">Password alone no longer grants a session.</span></div>
        ) : (
          <div className="stack">
            <p className="muted">
              Enrolment generates a secret and an <span className="mono">otpauth://</span> URI for your authenticator app.
              The secret is shown once and never returned by the API again. Activating MFA means the next sign-in
              will require a current code from that authenticator — for a demonstration account, enrol a throwaway
              identity rather than the shared demo logins.
            </p>
            <div className="row">
              <button className="btn" onClick={() => enroll.mutate()} disabled={enroll.isPending}>
                {enroll.isPending ? 'Generating…' : 'Begin enrolment'}
              </button>
            </div>
            {secret && (
              <div className="stack">
                <div className="mono small">{secret.otpauth_uri}</div>
                <div className="row">
                  <input placeholder="6-digit code" value={code} maxLength={6}
                         onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))} />
                  <button className="btn primary" onClick={() => activate.mutate(code)} disabled={code.length !== 6 || activate.isPending}>
                    Activate
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </Card>

      <Card title="Connector job ledger">
        <p className="muted small">Every ingest is recorded with its attempt history, backoff and terminal dead-letter state.</p>
        {jobs.error && <div className="banner warn">Job visibility requires administrator privileges.</div>}
        {jobs.isLoading && <Spinner />}
        {jobs.data && jobs.data.length === 0 && <p className="muted">No jobs recorded yet. Run an ingest from Data Sources to populate the ledger.</p>}
        {jobs.data && jobs.data.length > 0 && (
          <table className="table">
            <thead><tr><th>Job</th><th>Status</th><th>Attempts</th><th>Last error</th><th>Created</th></tr></thead>
            <tbody>
              {jobs.data.map((j) => (
                <tr key={j.id}>
                  <td className="mono small">{j.id.slice(0, 8)}<div className="muted small">{j.kind}</div></td>
                  <td><Badge tone={j.status === 'dead_letter' ? 'danger' : j.status === 'succeeded' ? 'ok' : 'warn'}>{j.status}</Badge></td>
                  <td>{j.attempts}/{j.max_attempts}</td>
                  <td className="small">{j.last_error ? j.last_error.slice(0, 90) : <span className="muted">—</span>}</td>
                  <td className="small">{fmtDate(j.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </Section>
  )
}
