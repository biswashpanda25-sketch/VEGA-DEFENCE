import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type User = {
  id: string; email: string; full_name: string; role: string
  organization_id: string | null; is_active: boolean
  clearance?: string; mfa_enabled?: boolean
}

type AuthState = {
  token: string | null
  user: User | null
  setAuth: (token: string, user: User) => void
  clear: () => void
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      clear: () => set({ token: null, user: null }),
    }),
    { name: 'vega-session' },
  ),
)

type UIState = {
  panel: { kind: string; title: string; data: any } | null
  openPanel: (p: { kind: string; title: string; data: any }) => void
  closePanel: () => void
  toast: string | null
  notify: (m: string) => void
  theme: 'light' | 'dark'
  toggleTheme: () => void
}

const initialTheme = (typeof window !== 'undefined' && localStorage.getItem('vega-theme') === 'light') ? 'light' : 'dark'
if (typeof document !== 'undefined') {
  document.documentElement.setAttribute('data-theme', initialTheme)
}

export const useUI = create<UIState>((set, get) => ({
  panel: null,
  openPanel: (p) => set({ panel: p }),
  closePanel: () => set({ panel: null }),
  toast: null,
  notify: (m) => {
    set({ toast: m })
    setTimeout(() => set({ toast: null }), 3200)
  },
  theme: initialTheme,
  toggleTheme: () => {
    const next = get().theme === 'dark' ? 'light' : 'dark'
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', next)
      localStorage.setItem('vega-theme', next)
    }
    set({ theme: next })
  },
}))
