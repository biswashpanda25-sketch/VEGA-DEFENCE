import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAuth } from '../store'
import { canAccessAdmin } from '../navigation/navConfig'
import { Card, Section, SyntheticBanner, Badge } from '../components/ui'
import Admin from './Admin'
import Governance from './Governance'
import Audit from './Audit'

export default function AdminPage() {
  const [params, setParams] = useSearchParams()
  const activeTab = (params.get('tab') as 'users' | 'orgs' | 'governance' | 'audit' | 'health') || 'users'
  const user = useAuth((s) => s.user)

  // Strict role gate
  const hasAccess = canAccessAdmin(user?.role)

  if (!hasAccess) {
    return (
      <Section
        title="Administration (Restricted)"
        sub="Governance, identity and security controls are restricted to authorized administrators and auditors."
      >
        <SyntheticBanner />
        <Card title="Access Denied: Clearance Boundary Enforced">
          <div className="banner crit" style={{ padding: '16px' }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>Administrative Clearance Required</div>
              <p style={{ marginTop: 6, lineHeight: 1.6 }}>
                Your current role (<strong>{user?.role || 'unassigned'}</strong>) does not have clearance
                to access administration, user management, or security audit logs.
              </p>
              <div className="tiny muted" style={{ marginTop: 8 }}>
                This access restriction is recorded in the platform audit trail under security policy §4.
              </div>
            </div>
          </div>
        </Card>
      </Section>
    )
  }

  return (
    <Section
      title="Platform Administration &amp; Governance"
      sub="Identity management, tenant isolation, cryptographic audit verification, and platform health."
      actions={<Badge tone="blue">Role: {user?.role}</Badge>}
    >
      <SyntheticBanner />

      <div className="tabs">
        <button
          className={`tab${activeTab === 'users' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'users' })}
        >
          Users &amp; Roles
        </button>
        <button
          className={`tab${activeTab === 'orgs' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'orgs' })}
        >
          Organisations &amp; Commands
        </button>
        <button
          className={`tab${activeTab === 'governance' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'governance' })}
        >
          Data Governance &amp; Clearance
        </button>
        <button
          className={`tab${activeTab === 'audit' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'audit' })}
        >
          Security &amp; Audit Log
        </button>
        <button
          className={`tab${activeTab === 'health' ? ' active' : ''}`}
          onClick={() => setParams({ tab: 'health' })}
        >
          Platform Health &amp; Connectors
        </button>
      </div>

      {activeTab === 'users' && <Admin defaultTab="users" />}
      {activeTab === 'orgs' && <Admin defaultTab="users" showOrgsOnly />}
      {activeTab === 'governance' && <Governance />}
      {activeTab === 'audit' && <Audit />}
      {activeTab === 'health' && <Admin defaultTab="system" />}
    </Section>
  )
}
