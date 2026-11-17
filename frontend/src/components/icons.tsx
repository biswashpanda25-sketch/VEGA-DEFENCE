import React from 'react'

type P = { size?: number; className?: string; style?: React.CSSProperties }
const s = (size = 16, style?: React.CSSProperties) => ({
  width: size, height: size, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', strokeWidth: 1.7, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const,
  style,
})

export const IcOverview = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><rect x="3" y="3" width="7" height="9" /><rect x="14" y="3" width="7" height="5" /><rect x="14" y="12" width="7" height="9" /><rect x="3" y="16" width="7" height="5" /></svg>
)
export const IcSource = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><ellipse cx="12" cy="5" rx="8" ry="3" /><path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5" /><path d="M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7" /></svg>
)
export const IcCatalog = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="M4 4h11a2 2 0 0 1 2 2v14H6a2 2 0 0 1-2-2V4z" /><path d="M17 8h3v12H8" /><path d="M8 8h5M8 12h5" /></svg>
)
export const IcSearch = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
)
export const IcGraph = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><circle cx="6" cy="6" r="2.5" /><circle cx="18" cy="7" r="2.5" /><circle cx="12" cy="18" r="2.5" /><path d="M8.2 7.5 15.8 7.9M7.4 8.2l3.5 7.4M16.6 9.2l-3.4 6.4" /></svg>
)
export const IcCase = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><rect x="3" y="7" width="18" height="13" rx="1.5" /><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 12h18" /></svg>
)
export const IcMap = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6z" /><path d="M9 3v15M15 6v15" /></svg>
)
export const IcOps = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="M12 2 3 7v10l9 5 9-5V7l-9-5z" /><path d="M12 12 3 7M12 12v10M12 12l9-5" /></svg>
)
export const IcAI = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="M12 3v3M12 18v3M4.2 7.5l2.6 1.5M17.2 15l2.6 1.5M4.2 16.5l2.6-1.5M17.2 9l2.6-1.5" /><circle cx="12" cy="12" r="4" /></svg>
)
export const IcReport = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg>
)
export const IcBell = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="M18 16V11a6 6 0 1 0-12 0v5l-2 3h16l-2-3z" /><path d="M10 22h4" /></svg>
)
export const IcAdmin = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2V21a2 2 0 1 1-4 0v-.1A1.7 1.7 0 0 0 7 19.4a1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0-1.2-2.9H1a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 2.6 7a1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H7a1.7 1.7 0 0 0 1-1.5V1a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V7a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" /></svg>
)
export const IcAudit = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="M12 2 4 5v6c0 5 3.4 9.7 8 11 4.6-1.3 8-6 8-11V5l-8-3z" /><path d="m9 12 2 2 4-4" /></svg>
)
export const IcWorkspace = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="M3 20h18M6 20V9l6-4 6 4v11" /><path d="M10 20v-5h4v5" /></svg>
)
export const IcChevron = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="m9 6 6 6-6 6" /></svg>
)
export const IcClose = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="M18 6 6 18M6 6l12 12" /></svg>
)
export const IcPlus = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="M12 5v14M5 12h14" /></svg>
)
export const IcDownload = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="M12 3v12M7 11l5 5 5-5M4 21h16" /></svg>
)
export const IcLogout = ({ size, className }: P) => (
  <svg {...s(size)} className={className}><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="m16 17 5-5-5-5M21 12H9" /></svg>
)
export const IcShield = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="M12 2 4 5v6c0 5 3.4 9.7 8 11 4.6-1.3 8-6 8-11V5l-8-3z" /></svg>
)
export const IcEye = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" /><circle cx="12" cy="12" r="3" /></svg>
)
export const IcEyeOff = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" /><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68" /><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61" /><line x1="2" x2="22" y1="2" y2="22" /></svg>
)
export const IcLock = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><rect width="18" height="11" x="3" y="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
)
export const IcKey = ({ size, className, style }: P) => (
  <svg {...s(size, style)} className={className}><path d="m21 2-2 2m-1.5 1.5L14 9l-2.5-2.5L10 8 8 6l-6 6 4 4 11-11Z" /><circle cx="17.5" cy="6.5" r="2.5" /></svg>
)
