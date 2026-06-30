import { getUser, logout } from '../lib/auth.js'

export default function TopBar({ dark, onToggleDark }) {
  const user = getUser()

  return (
    <header className="fixed top-0 left-0 right-0 h-topbar bg-surface/90 backdrop-blur border-b border-border flex items-center px-5 gap-3 z-50">
      <div className="flex items-center gap-2 w-sidebar pr-3">
        <div className="w-6 h-6 rounded-[6px] bg-accent flex items-center justify-center text-white text-[10px] font-black flex-shrink-0">JF</div>
        <span className="text-[15px] font-black tracking-tight">Jobs<em className="text-accent not-italic">Fit</em>AI</span>
      </div>

      <div className="flex-1" />

      <div className="flex items-center gap-2">
        {user?.email && (
          <span className="text-xs text-t3 hidden sm:block">{user.email}</span>
        )}

        <button
          onClick={onToggleDark}
          className="p-1.5 rounded-s text-t2 hover:text-t1 hover:bg-hover transition-colors"
          title="Toggle theme"
        >
          {dark ? (
            <svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
              <circle cx="10" cy="10" r="4"/><path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.9 4.9l1.4 1.4M13.7 13.7l1.4 1.4M4.9 15.1l1.4-1.4M13.7 6.3l1.4-1.4"/>
            </svg>
          ) : (
            <svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
              <path d="M17.5 12.5A7.5 7.5 0 017.5 2.5a7.5 7.5 0 100 15 7.5 7.5 0 0010-5z"/>
            </svg>
          )}
        </button>

        <button
          onClick={logout}
          className="text-xs text-t2 hover:text-t1 px-2.5 py-1.5 rounded-s hover:bg-hover transition-colors"
        >
          Sign out
        </button>
      </div>
    </header>
  )
}
