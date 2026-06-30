import { getUser, logout } from '../lib/auth.js'

export default function TopBar() {
  const user = getUser()

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 flex items-center px-4 border-b border-border bg-surface/90 backdrop-blur-md"
      style={{ height: 'var(--topbar-h)' }}
    >
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
