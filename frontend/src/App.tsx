import { useEffect } from 'react'
import { Navigate, Route, Routes, useSearchParams } from 'react-router-dom'
import { api } from './api'
import { useAuth, useUI } from './store'
import Login from './pages/Login'
import Topbar from './layouts/Topbar'
import Sidebar from './layouts/Sidebar'

// New 5 primary pages + 1 restricted administration page
import HomePage from './pages/HomePage'
import DataPage from './pages/DataPage'
import AskVegaPage from './pages/AskVegaPage'
import ExplorePage from './pages/ExplorePage'
import InvestigationsPage from './pages/InvestigationsPage'
import AdminPage from './pages/AdminPage'

function LegacySearchRedirect() {
  const [params] = useSearchParams()
  const q = params.get('q') || ''
  return <Navigate to={`/ask?tab=search${q ? `&q=${encodeURIComponent(q)}` : ''}`} replace />
}

function LegacyCaseRedirect() {
  const [params] = useSearchParams()
  const id = params.get('caseId') || params.get('id') || ''
  return <Navigate to={`/investigations${id ? `?caseId=${encodeURIComponent(id)}` : ''}`} replace />
}

export default function App() {
  const { token, setAuth, clear } = useAuth()
  const { panel, closePanel, toast } = useUI()

  useEffect(() => {
    if (!token) return
    api.get<any>('/auth/me').then((u) => setAuth(token, u)).catch(() => clear())
  }, [token])

  if (!token) return <Login />

  return (
    <div className="shell">
      <Topbar />
      <Sidebar />

      <main className="main">
        <div className={`canvas${panel ? ' with-panel' : ''}`}>
          <div className="content">
            <Routes>
              {/* Primary 5 Everyday Workspaces */}
              <Route path="/" element={<HomePage />} />
              <Route path="/data" element={<DataPage />} />
              <Route path="/ask" element={<AskVegaPage />} />
              <Route path="/explore" element={<ExplorePage />} />
              <Route path="/investigations" element={<InvestigationsPage />} />

              {/* Restricted Administration & Governance */}
              <Route path="/admin" element={<AdminPage />} />

              {/* Legacy Route Aliases & Redirects (Preserving Parameters) */}
              <Route path="/sources" element={<Navigate to="/data?tab=add" replace />} />
              <Route path="/catalog" element={<Navigate to="/data?tab=records" replace />} />
              <Route path="/assistant" element={<Navigate to="/ask" replace />} />
              <Route path="/search" element={<LegacySearchRedirect />} />
              <Route path="/geo" element={<Navigate to="/explore?tab=map" replace />} />
              <Route path="/graph" element={<Navigate to="/explore?tab=connections" replace />} />
              <Route path="/workspaces" element={<LegacyCaseRedirect />} />
              <Route path="/cases" element={<LegacyCaseRedirect />} />
              <Route path="/reports" element={<Navigate to="/investigations?tab=reports" replace />} />
              <Route path="/operations" element={<Navigate to="/?tab=operations" replace />} />
              <Route path="/notifications" element={<Navigate to="/?tab=activity" replace />} />
              <Route path="/governance" element={<Navigate to="/admin?tab=governance" replace />} />
              <Route path="/audit" element={<Navigate to="/admin?tab=audit" replace />} />

              {/* Catch-all fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>

          {/* Right-Hand Contextual Detail Drawer */}
          {panel && (
            <aside className="panel-right" aria-label="Record inspection panel">
              <div className="right-panel-head">
                <span className="eyebrow">{panel.kind}</span>
                <button className="btn sm ghost" onClick={closePanel}>Close</button>
              </div>
              <h3 style={{ fontSize: 14, marginBottom: 4 }}>{panel.title}</h3>
              <div className="stack gap8" style={{ marginTop: 10 }}>{panel.data}</div>
            </aside>
          )}
        </div>
      </main>

      {/* Floating Toast Message */}
      {toast && <div className="toast">{toast}</div>}
    </div>
  )
}
