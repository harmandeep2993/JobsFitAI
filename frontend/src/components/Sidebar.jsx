const tabs = [
  {
    id: 'analyzer',
    label: 'Analyzer',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="10" cy="10" r="8"/><path d="M10 6v4l3 3"/>
      </svg>
    ),
  },
  {
    id: 'matches',
    label: 'Job Matches',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 17l4-4 3 3 5-8 4 4"/>
      </svg>
    ),
  },
  {
    id: 'resumes',
    label: 'Resumes',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <rect x="4" y="2" width="12" height="16" rx="2"/>
        <line x1="7" y1="7" x2="13" y2="7"/>
        <line x1="7" y1="10" x2="13" y2="10"/>
        <line x1="7" y1="13" x2="10" y2="13"/>
      </svg>
    ),
  },
  {
    id: 'ats',
    label: 'ATS Check',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <path d="M8 1L2 4v4c0 3.3 2.5 5.8 6 7 3.5-1.2 6-3.7 6-7V4L8 1z"/>
        <polyline points="5.5,10 7.5,12 12,7"/>
      </svg>
    ),
  },
  {
    id: 'history',
    label: 'History',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 10a7 7 0 107-7H3"/><path d="M3 6V3l3 3-3 3"/>
        <path d="M10 7v3l2 2"/>
      </svg>
    ),
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="10" cy="10" r="2.5"/>
        <path d="M10 1v2M10 17v2M1 10h2M17 10h2M3.5 3.5l1.4 1.4M15.1 15.1l1.4 1.4M3.5 16.5l1.4-1.4M15.1 4.9l1.4-1.4"/>
      </svg>
    ),
  },
]

export default function Sidebar({ active, onChange }) {
  return (
    <aside className="fixed top-topbar left-0 bottom-0 w-sidebar bg-surface border-r border-border flex flex-col z-40">
      <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => onChange(t.id)}
            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-s text-[13px] font-medium transition-colors text-left ${
              active === t.id
                ? 'bg-accent/10 text-accent'
                : 'text-t2 hover:text-t1 hover:bg-hover'
            }`}
          >
            <span className={active === t.id ? 'text-accent' : 'text-t3'}>{t.icon}</span>
            {t.label}
          </button>
        ))}
      </nav>
    </aside>
  )
}
