import {
  IcOverview,
  IcSource,
  IcAI,
  IcMap,
  IcCase,
  IcAdmin,
} from '../components/icons'

export interface NavItem {
  to: string
  label: string
  key: string
  icon: any
  description?: string
}

export const PRIMARY_NAV: NavItem[] = [
  { to: '/', label: 'Home', key: 'home', icon: IcOverview, description: 'Overview and priorities' },
  { to: '/data', label: 'Data', key: 'data', icon: IcSource, description: 'Add, inspect and validate records' },
  { to: '/ask', label: 'Ask VEGA', key: 'ask', icon: IcAI, description: 'Natural-language intelligence and search' },
  { to: '/explore', label: 'Explore', key: 'explore', icon: IcMap, description: 'Map, connections, records and timelines' },
  { to: '/investigations', label: 'Investigations', key: 'investigations', icon: IcCase, description: 'Cases, evidence, findings and SITREPs' },
]

export const ADMIN_NAV: NavItem & { allowedRoles: string[] } = {
  to: '/admin',
  label: 'Administration',
  key: 'admin',
  icon: IcAdmin,
  description: 'Users, organisations, governance, audit and health',
  allowedRoles: ['platform_admin', 'org_admin', 'data_admin', 'reviewer', 'auditor'],
}

export function canAccessAdmin(role?: string | null): boolean {
  if (!role) return false
  return ADMIN_NAV.allowedRoles.includes(role)
}
