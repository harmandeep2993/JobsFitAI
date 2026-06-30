import { useState } from 'react'
import { ToastProvider } from '../components/Toast.jsx'
import TopBar from '../components/TopBar.jsx'
import Sidebar from '../components/Sidebar.jsx'
import Analyzer from '../components/tabs/Analyzer.jsx'
import JobMatches from '../components/tabs/JobMatches.jsx'
import Resumes from '../components/tabs/Resumes.jsx'
import ATS from '../components/tabs/ATS.jsx'
import History from '../components/tabs/History.jsx'
import Settings from '../components/tabs/Settings.jsx'

const TAB_COMPONENTS = {
  analyzer: Analyzer,
  matches:  JobMatches,
  resumes:  Resumes,
  ats:      ATS,
  history:  History,
  settings: Settings,
}

export default function AppShell({ dark, onToggleDark }) {
  const [tab, setTab] = useState('analyzer')
  const TabContent = TAB_COMPONENTS[tab] || Analyzer

  return (
    <ToastProvider>
      <div className="min-h-screen bg-bg text-t1">
        <TopBar dark={dark} onToggleDark={onToggleDark} />
        <Sidebar active={tab} onChange={setTab} />
        <main
          className="pt-topbar pl-sidebar min-h-screen"
          style={{ paddingLeft: 'var(--sidebar-w)' }}
        >
          <div className="p-6 max-w-5xl mx-auto">
            <TabContent />
          </div>
        </main>
      </div>
    </ToastProvider>
  )
}
