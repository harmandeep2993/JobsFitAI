import { getUser, logout } from '../lib/auth.js'

export default function TopBar({ dark, onToggleDark }) {
  const user = getUser()

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 flex items-center px-4 border-b border-border bg-surface/90 backdrop-blur-md"
      style={{ height: 'var(--topbar-h)' }}
    >
      {/* Brand - aligned with sidebar width */}
      <div
        className="flex items-center gap-2.5 flex-shrink-0"
        style={{ width: 'var(--sidebar-w)', paddingRight: '16px' }}
      >
        <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center flex-shrink-0">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="white">
            <path d="M8 1L1 4.5v4c0 3.5 2.8 6.2 7 7.5 4.2-1.3 7-4 7-7.5v-4L8 1z"/>
          </svg>
        </div>
        <span className="text-[15px] font-bold tracking-tight text-t1">
          Jobs<span className="text-accent">Fit</span>AI
        </span>
      </div>

      <div className="flex-1" />

      <div className="flex items-center gap-1">
        {user?.email && (
          <span className="text-[12px] text-t3 mr-2 hidden sm:block max-w-[180px] truncate">
            {user.email}
          </span>
        )}

        {/* Theme toggle */}
        <button
          onClick={onToggleDark}
          className="w-8 h-8 flex items-center justify-center rounded-sm text-t3 hover:text-t1 hover:bg-hover transition-colors"
          title="Toggle theme"
        >
          {dark ? (
            <svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="10" cy="10" r="4"/>
              <path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.9 4.9l1.4 1.4M13.7 13.7l1.4 1.4M4.9 15.1l1.4-1.4M13.7 6.3l1.4-1.4"/>
            </svg>
          ) : (
            <svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M17.5 12.5A7.5 7.5 0 017.5 2.5a7.5 7.5 0 100 15 7.5 7.5 0 0010-5z"/>
            </svg>
          )}
        </button>

        {/* Sign out */}
        <button
          onClick={logout}
          className="h-8 px-3 text-[12.5px] font-medium text-t2 hover:text-t1 hover:bg-hover rounded-sm transition-colors"
        >
          Sign out
        </button>
      </div>
    </header>
  )
}
