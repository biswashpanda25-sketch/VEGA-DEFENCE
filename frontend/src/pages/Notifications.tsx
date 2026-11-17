import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, fmtDate } from '../api'
import { Badge, Card, Empty, ErrorBox, Section, Spinner } from '../components/ui'
import { useUI } from '../store'

export default function Notifications() {
  const qc = useQueryClient()
  const notify = useUI((s) => s.notify)
  const list = useQuery({ queryKey: ['notifications'], queryFn: () => api.get<any[]>('/notifications') })
  const read = useMutation({
    mutationFn: (id: string) => api.post<any>(`/notifications/${id}/read`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['notifications'] }); notify('Marked as read') },
  })

  const unread = (list.data ?? []).filter((n) => !n.is_read)

  return (
    <Section
      title="Notifications"
      sub="Operational alerts, data quality warnings and approval requests for your organization. External channels (email, webhook) require configured institutional endpoints."
      actions={<span className="tiny muted">{unread.length} unread</span>}
    >
      {list.error && <ErrorBox error={list.error} />}
      <div className="grid g-2-1">
        <Card title="Alert stream" bodyStyle={{ padding: 0 }}>
          {list.isLoading ? <Spinner /> : (
            <div>
              {(list.data ?? []).map((n) => (
                <div key={n.id} style={{
                  padding: '10px 13px', borderBottom: '1px solid var(--line)',
                  background: n.is_read ? 'transparent' : 'rgba(213,161,60,.06)',
                  borderLeft: `2px solid ${n.is_read ? 'transparent' : 'var(--accent)'}`,
                }}>
                  <div className="row between gap8">
                    <span style={{ fontSize: 12.5 }}>{n.title}</span>
                    <div className="row gap6">
                      <Badge>{n.severity}</Badge>
                      {!n.is_read && <button className="btn sm ghost" onClick={() => read.mutate(n.id)}>Mark read</button>}
                    </div>
                  </div>
                  <div className="tiny dim" style={{ marginTop: 3 }}>{n.message}</div>
                  <div className="tiny muted">{fmtDate(n.created_at)}</div>
                </div>
              ))}
              {(list.data ?? []).length === 0 && <Empty>No notifications</Empty>}
            </div>
          )}
        </Card>

        <div className="stack gap12">
          <Card title="Delivery channels">
            <div className="stack gap8">
              <div className="row between"><span className="tiny">In-application</span><Badge tone="green">active</Badge></div>
              <div className="row between"><span className="tiny">Email</span><Badge tone="neutral">not configured</Badge></div>
              <div className="row between"><span className="tiny">Authorized webhook</span><Badge tone="neutral">not configured</Badge></div>
            </div>
            <div className="tiny muted" style={{ marginTop: 9 }}>
              Channel adapters exist in the notification service interface; delivery is only claimed where an
              institutional endpoint and credentials have been verified.
            </div>
          </Card>
          <Card title="Alert rules">
            <div className="stack gap6 tiny muted">
              <div>• Asset status transition to degraded / offline</div>
              <div>• Ingestion failure or duplicate spike</div>
              <div>• Records missing district or provenance fields</div>
              <div>• Finding awaiting reviewer decision</div>
              <div>• Connector health change</div>
            </div>
            <div className="tiny muted" style={{ marginTop: 9 }}>
              Thresholds, deduplication keys and escalation policies are organization-configurable. The demonstration
              dataset includes seeded examples of quality and status alerts.
            </div>
          </Card>
        </div>
      </div>
    </Section>
  )
}
