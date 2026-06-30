const NAV_ITEMS = [
  {
    id: 'analyzer',
    label: 'Analyzer',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="9" cy="9" r="6.5"/>
        <path d="M14 14l3.5 3.5"/>
        <path d="M9 6v3l2 2"/>
      </svg>
    ),
  },
  {
    id: 'matches',
    label: 'Job Matches',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 10h16M2 5h10M2 15h7"/>
        <circle cx="15" cy="14" r="3"/>
        <path d="M13.5 14l1 1 2-2"/>
      </svg>
    ),
  },
  {
    id: 'resumes',
    label: 'Resumes',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="4" y="2" width="12" height="16" rx="2"/>
        <path d="M8 7h4M8 10h4M8 13h2"/>
      </svg>
    ),
  },
  {
    id: 'ats',
    label: 'ATS Check',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M8.5 1.5L2 5v4.5c0 3.5 2.8 6.2 6.5 7.5 3.7-1.3 6.5-4 6.5-7.5V5L8.5 1.5z"/>
        <polyline points="6,10 8,12 12.5,7.5"/>
      </svg>
    ),
  },
  {
    id: 'history',
    label: 'History',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3.5 9.5A6.5 6.5 0 1110 3.5H3.5"/>
        <path d="M3.5 5.5v4h4"/>
        <path d="M10 7v3l2.5 2"/>
      </svg>
    ),
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="10" cy="10" r="2.5"/>
        <path d="M10 1v2M10 17v2M1 10h2M17 10h2M3.5 3.5l1.4 1.4M15.1 15.1l1.4 1.4M3.5 16.5l1.4-1.4M15.1 4.9l1.4-1.4"/>
      </svg>
    ),
  },
]

export default function Sidebar({ active, onChange }) {
  return (
    <aside
      className="fixed left-0 bottom-0 border-r border-border bg-surface z-40 flex flex-col"
      style={{ top: 'var(--topbar-h)', width: 'var(--sidebar-w)' }}
    >
      <nav className="flex-1 p-2 overflow-y-auto">
        {NAV_ITEMS.map(item => {
          const isActive = active === item.id
          return (
            <button
              key={item.id}
              onClick={() => onChange(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 mb-0.5 rounded-sm text-[13.5px] font-medium transition-all text-left group ${
                isActive
                  ? 'bg-accent/10 text-accent'
                  : 'text-t2 hover:text-t1 hover:bg-hover'
              }`}
            >
              <span className={`flex-shrink-0 transition-colors ${isActive ? 'text-accent' : 'text-t3 group-hover:text-t2'}`}>
                {item.icon}
              </span>
              <span>{item.label}</span>
              {isActive && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-accent flex-shrink-0" />
              )}
            </button>
          )
        })}
      </nav>

      <div className="p-3 border-t border-border">
        <div className="text-[11px] text-t3 text-center">JobsFitAI</div>
      </div>
    </aside>
  )
}
